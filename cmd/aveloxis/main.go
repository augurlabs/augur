// Aveloxis is a data collection tool for open source software community health metrics.
// It collects data from GitHub and GitLab with equal completeness, storing results
// in a shared schema for cross-platform analysis.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"os/signal"
	"slices"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/aveloxis/aveloxis/internal/api"
	"github.com/aveloxis/aveloxis/internal/collector"
	"github.com/aveloxis/aveloxis/internal/config"
	"github.com/aveloxis/aveloxis/internal/db"
	"github.com/aveloxis/aveloxis/internal/model"
	"github.com/aveloxis/aveloxis/internal/monitor"
	"github.com/aveloxis/aveloxis/internal/pidfile"
	"github.com/aveloxis/aveloxis/internal/platform"
	"github.com/aveloxis/aveloxis/internal/platform/github"
	"github.com/aveloxis/aveloxis/internal/platform/gitlab"
	"github.com/aveloxis/aveloxis/internal/scheduler"
	"github.com/aveloxis/aveloxis/internal/mailer"
	"github.com/aveloxis/aveloxis/internal/web"
	"github.com/spf13/cobra"
)

// Version is the current Aveloxis version. Single source of truth is db.ToolVersion.
var Version = db.ToolVersion

func main() {
	root := &cobra.Command{
		Use:   "aveloxis",
		Short: "Open source community health data collection",
	}

	var cfgPath string
	root.PersistentFlags().StringVarP(&cfgPath, "config", "c", "aveloxis.json", "path to config file")

	root.AddCommand(
		collectCmd(&cfgPath),
		serveCmd(&cfgPath),
		apiCmd(&cfgPath),
		webCmd(&cfgPath),
		startCmd(&cfgPath),
		stopCmd(&cfgPath),
		addRepoCmd(&cfgPath),
		importFoundationsCmd(&cfgPath),
		addKeyCmd(&cfgPath),
		prioritizeCmd(&cfgPath),
		recollectCmd(&cfgPath),
		migrateCmd(&cfgPath),
		refreshViewsCmd(&cfgPath),
		installToolsCmd(),
		sbomCmd(&cfgPath),
		shadowDiffCmd(),
		versionCmd(),
	)

	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}

// --- serve: long-running scheduler + monitor ---

func serveCmd(cfgPath *string) *cobra.Command {
	var (
		monitorAddr string
		workers     int
		useAugurKeys bool
	)

	cmd := &cobra.Command{
		Use:   "serve",
		Short: "Run the collection scheduler and monitoring dashboard",
		Long: `Starts the scheduler, which continuously collects data for all repos
in the queue. Also starts the web monitor (like Flower for Celery).

The queue is stored in Postgres. Multiple aveloxis instances can share
the same queue — each claims jobs via SELECT ... FOR UPDATE SKIP LOCKED.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			// If --workers wasn't explicitly set on the CLI, use the config
			// file value. This lets users set workers in aveloxis.json without
			// needing to pass it on the command line every time.
			if !cmd.Flags().Changed("workers") {
				cfg := loadConfig(*cfgPath, slog.New(slog.NewTextHandler(os.Stderr, nil)))
				if cfg.Collection.Workers > 0 {
					workers = cfg.Collection.Workers
				}
			}
			return runServe(*cfgPath, monitorAddr, workers, useAugurKeys)
		},
	}

	cmd.Flags().StringVar(&monitorAddr, "monitor", "127.0.0.1:5555", "address for the monitoring dashboard")
	cmd.Flags().IntVar(&workers, "workers", 1, "number of concurrent collection workers")
	cmd.Flags().BoolVar(&useAugurKeys, "augur-keys", false, "load API keys from Augur's augur_operations.worker_oauth table")

	return cmd
}

func runServe(cfgPath, monitorAddr string, workers int, useAugurKeys bool) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	// Write PID file so 'aveloxis stop serve' can find us.
	pidPath := pidfile.Path("serve")
	pidfile.Write(pidPath, os.Getpid())
	defer pidfile.Remove(pidPath)

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()

	// Scale the database connection pool to the worker count so collection
	// workers don't starve each other for connections. Each worker makes many
	// concurrent DB calls (inserts, queries) during collection phases.
	poolSize := max(int32(workers+15), 20)
	// application_name = "aveloxis-serve" so post-stop verification
	// (and operators reading pg_stat_activity) can filter per-process.
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionStringWithAppName("aveloxis-serve"), logger, poolSize)
	if err != nil {
		return fmt.Errorf("connecting to database: %w", err)
	}
	defer store.Close()

	if err := store.Migrate(ctx); err != nil {
		return fmt.Errorf("migrating database: %w", err)
	}

	ghKeys, glKeys, err := loadKeys(ctx, cfg, store, useAugurKeys, logger)
	if err != nil {
		return fmt.Errorf("loading API keys: %w", err)
	}
	ghClient := github.New(cfg.GitHub.BaseURL, ghKeys, logger)
	glClient := gitlab.New(cfg.GitLab.BaseURL, glKeys, logger)

	// Start scheduler.
	store.SetMatviewOnStartup(cfg.Collection.MatviewRebuildOnStartup)

	sched := scheduler.NewWithKeys(store, ghClient, glClient, ghKeys, logger, scheduler.Config{
		Workers:             workers,
		RecollectAfter:      time.Duration(cfg.Collection.DaysUntilRecollect) * 24 * time.Hour,
		RepoCloneDir:        cfg.Collection.RepoCloneDir,
		MatviewRebuildDay:   cfg.Collection.MatviewRebuildWeekday(),
		ForceFullCollection: cfg.Collection.ForceFullCollection,
		PRChildMode:         cfg.Collection.PRChildMode,
		ListingMode:         cfg.Collection.ListingMode,
		ThreadingMode:       cfg.Collection.ThreadingMode,
		ShardSize:           cfg.Collection.ShardSize,
		EnrichInterval:        cfg.Collection.EnrichIntervalDuration(),
		SearchResolveInterval: cfg.Collection.SearchResolveIntervalDuration(),
		AffiliationInterval:   cfg.Collection.AffiliationIntervalDuration(),
		ShutdownGrace:         cfg.Collection.ShutdownGraceDuration(),
	})
	go sched.Run(ctx)

	// Start monitor.
	mon := monitor.New(store, logger)
	srv := &http.Server{Addr: monitorAddr, Handler: mon.Handler()}
	go func() {
		logger.Info("monitor listening", "addr", monitorAddr)
		if err := srv.ListenAndServe(); err != http.ErrServerClosed {
			logger.Error("monitor server error", "error", err)
		}
	}()

	<-ctx.Done()
	srv.Shutdown(context.Background())
	return nil
}

// --- api: REST API server ---

func apiCmd(cfgPath *string) *cobra.Command {
	var addr string
	cmd := &cobra.Command{
		Use:   "api",
		Short: "Start the Aveloxis REST API server",
		Long: `Starts a REST API server for data access. Used by the monitoring
dashboard and web GUI to fetch repo statistics and SBOMs.

Run alongside 'aveloxis serve' and 'aveloxis web'.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runAPI(*cfgPath, addr)
		},
	}
	cmd.Flags().StringVar(&addr, "addr", "127.0.0.1:8383", "listen address for the API server")
	return cmd
}

func runAPI(cfgPath, addr string) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	pidPath := pidfile.Path("api")
	pidfile.Write(pidPath, os.Getpid())
	defer pidfile.Remove(pidPath)

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()

	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionStringWithAppName("aveloxis-api"), logger)
	if err != nil {
		return fmt.Errorf("connecting to database: %w", err)
	}
	defer store.Close()

	// api does not run migrations — check if schema is current.
	store.CheckSchemaVersion(ctx, logger)

	apiServer := api.New(store, logger)
	srv := &http.Server{Addr: addr, Handler: apiServer.Handler()}

	go func() {
		logger.Info("API server listening", "addr", addr)
		if err := srv.ListenAndServe(); err != http.ErrServerClosed {
			logger.Error("API server error", "error", err)
		}
	}()

	<-ctx.Done()
	srv.Shutdown(context.Background())
	return nil
}

// --- collect: one-shot collection ---

func collectCmd(cfgPath *string) *cobra.Command {
	var (
		full         bool
		useAugurKeys bool
	)

	cmd := &cobra.Command{
		Use:   "collect [repo-urls...]",
		Short: "One-shot collection for specific repos (does not use the queue)",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCollect(*cfgPath, args, full, useAugurKeys)
		},
	}

	cmd.Flags().BoolVar(&full, "full", false, "full historical collection")
	cmd.Flags().BoolVar(&useAugurKeys, "augur-keys", false, "load API keys from Augur's augur_operations.worker_oauth table")

	return cmd
}

func runCollect(cfgPath string, repoURLs []string, full, useAugurKeys bool) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()

	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return fmt.Errorf("connecting to database: %w", err)
	}
	defer store.Close()

	if err := store.Migrate(ctx); err != nil {
		return fmt.Errorf("migrating database: %w", err)
	}

	ghKeys, glKeys, err := loadKeys(ctx, cfg, store, useAugurKeys, logger)
	if err != nil {
		return fmt.Errorf("loading API keys: %w", err)
	}
	ghClient := github.New(cfg.GitHub.BaseURL, ghKeys, logger)
	glClient := gitlab.New(cfg.GitLab.BaseURL, glKeys, logger)

	var since time.Time
	if !full {
		since = time.Now().AddDate(0, 0, -cfg.Collection.DaysUntilRecollect)
	}

	for _, repoURL := range repoURLs {
		client, owner, repo, err := collector.ClientForRepo(repoURL, ghClient, glClient)
		if err != nil {
			logger.Error("skipping repo", "url", repoURL, "error", err)
			continue
		}

		repoID, err := store.UpsertRepo(ctx, &model.Repo{
			Platform: client.Platform(),
			GitURL:   repoURL,
			Name:     repo,
			Owner:    owner,
		})
		if err != nil {
			logger.Error("failed to upsert repo", "url", repoURL, "error", err)
			continue
		}

		coll := collector.NewWithOptions(client, store, logger, ghKeys, cfg.Collection.RepoCloneDir)
		result, err := coll.CollectRepo(ctx, repoID, owner, repo, since)
		if err != nil {
			logger.Error("collection failed", "url", repoURL, "error", err)
			continue
		}

		logger.Info("done", "url", repoURL,
			"issues", result.Issues, "prs", result.PullRequests,
			"messages", result.Messages, "events", result.Events,
			"releases", result.Releases, "contributors", result.Contributors,
			"errors", len(result.Errors))
	}
	return nil
}

// --- add-repo: add repos to the collection queue ---

func addRepoCmd(cfgPath *string) *cobra.Command {
	var (
		priority  int
		fromAugur bool
	)

	cmd := &cobra.Command{
		Use:   "add-repo [repo-urls...]",
		Short: "Add repos to the collection queue",
		Long: `Registers repos in the database and adds them to the scheduler queue.
The scheduler (aveloxis serve) will pick them up automatically.

Use --from-augur to import repos from an existing Augur installation's
augur_data.repo table. Each URL is verified against the forge (HTTP HEAD)
and only repos that still exist are imported.`,
		Args: func(cmd *cobra.Command, args []string) error {
			fromAugur, _ := cmd.Flags().GetBool("from-augur")
			if !fromAugur && len(args) == 0 {
				return fmt.Errorf("requires at least 1 repo URL (or --from-augur)")
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			if fromAugur {
				return runImportFromAugur(*cfgPath, priority)
			}
			return runAddRepo(*cfgPath, args, priority)
		},
	}

	cmd.Flags().IntVar(&priority, "priority", 100, "queue priority (lower = collected sooner, 0 = immediate)")
	cmd.Flags().BoolVar(&fromAugur, "from-augur", false, "import repos from augur_data.repo (verifies each URL exists)")

	return cmd
}

// isOrgURL checks if a URL points to a GitHub org or GitLab group (not a specific repo).
// Returns (isOrg, host, orgName, platform).
func isOrgURL(rawURL string) (bool, string, string, model.Platform) {
	rawURL = strings.TrimSpace(rawURL)
	rawURL = strings.TrimSuffix(rawURL, "/")
	u, err := url.Parse(rawURL)
	if err != nil {
		return false, "", "", 0
	}
	host := strings.ToLower(u.Host)
	path := strings.Trim(u.Path, "/")
	parts := strings.Split(path, "/")

	// GitHub org: https://github.com/chaoss (exactly 1 path segment)
	if (host == "github.com") && len(parts) == 1 && parts[0] != "" {
		return true, host, parts[0], model.PlatformGitHub
	}
	// GitLab group: could be 1+ segments, but we only treat it as a group
	// if ParseRepoURL fails (meaning it can't find a project at the end).
	// For now, we try ParseRepoURL first and fall through to org expansion.
	return false, "", "", 0
}

func runAddRepo(cfgPath string, repoURLs []string, priority int) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	ctx := context.Background()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return fmt.Errorf("connecting to database: %w", err)
	}
	defer store.Close()

	if err := store.Migrate(ctx); err != nil {
		return fmt.Errorf("migrating database: %w", err)
	}

	ghKeys, glKeys, err := loadKeys(ctx, cfg, store, false, logger)
	if err != nil {
		return fmt.Errorf("loading API keys: %w", err)
	}

	for _, repoURL := range repoURLs {
		// Check if this is an org/group URL instead of a repo URL.
		if isOrg, host, orgName, plat := isOrgURL(repoURL); isOrg {
			logger.Info("expanding organization", "org", orgName, "platform", plat)

			// Create a repo_group for this org so the refresh job can re-scan it later.
			rgType := "github_org"
			if plat == model.PlatformGitLab {
				rgType = "gitlab_group"
			}
			groupID, err := store.UpsertRepoGroup(ctx, orgName, rgType, repoURL)
			if err != nil {
				logger.Warn("failed to create repo group for org", "org", orgName, "error", err)
			}

			var repos []orgRepo
			switch plat {
			case model.PlatformGitHub:
				ghHTTP := platform.NewHTTPClient("https://api.github.com", ghKeys, logger, platform.AuthGitHub)
				repos, err = listGitHubOrgRepos(ctx, ghHTTP, orgName)
			case model.PlatformGitLab:
				glHTTP := platform.NewHTTPClient("https://"+host+"/api/v4", glKeys, logger, platform.AuthGitLab)
				repos, err = listGitLabGroupRepos(ctx, glHTTP, orgName)
			}
			if err != nil {
				logger.Error("failed to list org repos", "org", orgName, "error", err)
				continue
			}
			logger.Info("found repos in organization", "org", orgName, "count", len(repos))

			// Bridge legacy repo_groups discovery into modern
			// aveloxis_ops.user_repos so any user_group tracking this
			// org (via user_org_requests.org_url) gets every repo
			// (including forks — listGitHub/GitLab use ?type=all)
			// linked. Hoisted out of the per-repo loop so the lookup
			// runs once per scan.
			userGroupIDs, ugErr := store.GetUserGroupIDsForOrgURL(ctx, repoURL)
			if ugErr != nil {
				logger.Warn("failed to look up user_groups for org", "org_url", repoURL, "error", ugErr)
			}
			for _, r := range repos {
				addOneRepoWithGroup(ctx, store, logger, r.URL, r.Owner, r.Name, plat, priority, groupID)
				if len(userGroupIDs) == 0 {
					continue
				}
				repoID, ferr := store.FindRepoByURL(ctx, r.URL)
				if ferr != nil || repoID == 0 {
					continue
				}
				for _, gid := range userGroupIDs {
					if err := store.AddRepoToGroupByID(ctx, gid, repoID); err != nil {
						logger.Warn("failed to link repo into user_repos",
							"group_id", gid, "repo_id", repoID, "error", err)
					}
				}
			}
			continue
		}

		// Regular repo URL.
		parsed, err := platform.ParseRepoURL(repoURL)
		if err != nil {
			logger.Error("invalid URL", "url", repoURL, "error", err)
			continue
		}
		addOneRepo(ctx, store, logger, repoURL, parsed.Owner, parsed.Repo, parsed.Platform, priority)
	}
	return nil
}

func addOneRepoWithGroup(ctx context.Context, store *db.PostgresStore, logger *slog.Logger, repoURL, owner, name string, plat model.Platform, priority int, groupID int64) {
	repoID, err := store.UpsertRepo(ctx, &model.Repo{
		Platform: plat,
		GitURL:   repoURL,
		Name:     name,
		Owner:    owner,
		GroupID:  groupID,
	})
	if err != nil {
		logger.Error("failed to register repo", "url", repoURL, "error", err)
		return
	}
	if err := store.EnqueueRepo(ctx, repoID, priority); err != nil {
		logger.Error("failed to enqueue repo", "url", repoURL, "error", err)
		return
	}
	logger.Info("repo added to queue", "url", repoURL, "repo_id", repoID, "priority", priority)
}

func addOneRepo(ctx context.Context, store *db.PostgresStore, logger *slog.Logger, repoURL, owner, name string, plat model.Platform, priority int) {
	repoID, err := store.UpsertRepo(ctx, &model.Repo{
		Platform: plat,
		GitURL:   repoURL,
		Name:     name,
		Owner:    owner,
	})
	if err != nil {
		logger.Error("failed to register repo", "url", repoURL, "error", err)
		return
	}
	if err := store.EnqueueRepo(ctx, repoID, priority); err != nil {
		logger.Error("failed to enqueue repo", "url", repoURL, "error", err)
		return
	}
	logger.Info("repo added to queue", "url", repoURL, "repo_id", repoID, "priority", priority)
}

type orgRepo struct {
	URL   string
	Owner string
	Name  string
}

// listGitHubOrgRepos calls GET /orgs/{org}/repos to list all public repos.
func listGitHubOrgRepos(ctx context.Context, http *platform.HTTPClient, org string) ([]orgRepo, error) {
	var repos []orgRepo
	page := 1
	for {
		path := fmt.Sprintf("/orgs/%s/repos?per_page=100&type=all&page=%d", org, page)
		resp, err := http.Get(ctx, path)
		if err != nil {
			return repos, err
		}
		var items []struct {
			FullName string `json:"full_name"`
			HTMLURL  string `json:"html_url"`
			Name     string `json:"name"`
			Owner    struct {
				Login string `json:"login"`
			} `json:"owner"`
			Archived bool `json:"archived"`
			Fork     bool `json:"fork"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&items); err != nil {
			resp.Body.Close()
			return repos, err
		}
		resp.Body.Close()

		if len(items) == 0 {
			break
		}
		for _, item := range items {
			repos = append(repos, orgRepo{
				URL:   item.HTMLURL,
				Owner: item.Owner.Login,
				Name:  item.Name,
			})
		}
		page++
	}
	return repos, nil
}

// listGitLabGroupRepos calls GET /groups/{group}/projects to list all projects.
func listGitLabGroupRepos(ctx context.Context, http *platform.HTTPClient, group string) ([]orgRepo, error) {
	var repos []orgRepo
	page := 1
	encodedGroup := url.PathEscape(group)
	for {
		path := fmt.Sprintf("/groups/%s/projects?per_page=100&include_subgroups=true&page=%d", encodedGroup, page)
		resp, err := http.Get(ctx, path)
		if err != nil {
			return repos, err
		}
		var items []struct {
			PathWithNamespace string `json:"path_with_namespace"`
			WebURL            string `json:"web_url"`
			Name              string `json:"name"`
			Namespace         struct {
				FullPath string `json:"full_path"`
			} `json:"namespace"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&items); err != nil {
			resp.Body.Close()
			return repos, err
		}
		resp.Body.Close()

		if len(items) == 0 {
			break
		}
		for _, item := range items {
			repos = append(repos, orgRepo{
				URL:   item.WebURL,
				Owner: item.Namespace.FullPath,
				Name:  item.Name,
			})
		}
		page++
	}
	return repos, nil
}

func runImportFromAugur(cfgPath string, priority int) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	ctx := context.Background()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return fmt.Errorf("connecting to database: %w", err)
	}
	defer store.Close()

	if err := store.Migrate(ctx); err != nil {
		return fmt.Errorf("migrating database: %w", err)
	}

	// Read all repos from Augur.
	augurRepos, err := db.LoadAugurRepos(ctx, store.Pool())
	if err != nil {
		return fmt.Errorf("reading Augur repos: %w", err)
	}
	logger.Info("found repos in augur_data.repo", "count", len(augurRepos))

	httpClient := &http.Client{Timeout: 10 * time.Second}
	var imported, skipped, failed int

	for _, ar := range augurRepos {
		// Parse the URL to determine platform and owner/repo.
		parsed, err := platform.ParseRepoURL(ar.RepoGit)
		if err != nil {
			logger.Warn("skipping unparseable URL", "url", ar.RepoGit, "augur_repo_id", ar.RepoID, "error", err)
			skipped++
			continue
		}

		// Verify the repo still exists on the forge with an HTTP HEAD.
		exists, err := verifyRepoExists(ctx, httpClient, ar.RepoGit)
		if err != nil {
			logger.Warn("error verifying repo", "url", ar.RepoGit, "error", err)
			failed++
			continue
		}
		if !exists {
			logger.Warn("repo no longer exists on forge, skipping", "url", ar.RepoGit)
			skipped++
			continue
		}

		// Import into Aveloxis.
		repoID, err := store.UpsertRepo(ctx, &model.Repo{
			Platform: parsed.Platform,
			GitURL:   ar.RepoGit,
			Name:     parsed.Repo,
			Owner:    parsed.Owner,
		})
		if err != nil {
			logger.Error("failed to register repo", "url", ar.RepoGit, "error", err)
			failed++
			continue
		}

		if err := store.EnqueueRepo(ctx, repoID, priority); err != nil {
			logger.Error("failed to enqueue repo", "url", ar.RepoGit, "error", err)
			failed++
			continue
		}

		imported++
		logger.Info("imported repo", "url", ar.RepoGit, "repo_id", repoID)
	}

	logger.Info("import complete",
		"imported", imported,
		"skipped", skipped,
		"failed", failed,
		"total_augur_repos", len(augurRepos),
	)
	return nil
}

// verifyRepoExists checks that a repo URL resolves on the forge.
// Uses HTTP HEAD to avoid downloading the full page.
func verifyRepoExists(ctx context.Context, client *http.Client, repoURL string) (bool, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodHead, repoURL, nil)
	if err != nil {
		return false, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return false, err
	}
	resp.Body.Close()
	// 200 = exists. 301/302 = moved (still exists). 404/410 = gone.
	return resp.StatusCode >= 200 && resp.StatusCode < 400, nil
}

// --- add-key: store API keys in the database ---

func addKeyCmd(cfgPath *string) *cobra.Command {
	var (
		plat      string
		name      string
		fromAugur bool
	)

	cmd := &cobra.Command{
		Use:   "add-key [token]",
		Short: "Store API keys in the database",
		Long: `Stores GitHub or GitLab API tokens in aveloxis_ops.worker_oauth.
Keys stored here are loaded automatically by 'aveloxis serve' and 'aveloxis collect'.

Use --from-augur to copy all keys from augur_operations.worker_oauth into
aveloxis_ops.worker_oauth in one shot. Duplicates are skipped.`,
		Args: func(cmd *cobra.Command, args []string) error {
			fromAugur, _ := cmd.Flags().GetBool("from-augur")
			if !fromAugur && len(args) != 1 {
				return fmt.Errorf("requires exactly 1 token argument (or --from-augur)")
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			if fromAugur {
				return runImportKeysFromAugur(*cfgPath)
			}
			return runAddKey(*cfgPath, args[0], plat, name)
		},
	}

	cmd.Flags().StringVar(&plat, "platform", "github", "platform for this key (github or gitlab)")
	cmd.Flags().StringVar(&name, "name", "", "optional label for this key")
	cmd.Flags().BoolVar(&fromAugur, "from-augur", false, "copy all keys from augur_operations.worker_oauth")

	return cmd
}

func runAddKey(cfgPath, token, plat, name string) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	if plat != "github" && plat != "gitlab" {
		return fmt.Errorf("platform must be 'github' or 'gitlab', got %q", plat)
	}

	ctx := context.Background()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return err
	}
	defer store.Close()

	if err := store.Migrate(ctx); err != nil {
		return err
	}

	if err := db.SaveAPIKey(ctx, store.Pool(), name, token, plat); err != nil {
		return fmt.Errorf("saving key: %w", err)
	}

	masked := token[:4] + "..." + token[len(token)-4:]
	logger.Info("key stored", "platform", plat, "token", masked)
	return nil
}

func runImportKeysFromAugur(cfgPath string) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	ctx := context.Background()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return err
	}
	defer store.Close()

	if err := store.Migrate(ctx); err != nil {
		return err
	}

	imported, err := db.ImportKeysFromAugur(ctx, store.Pool())
	if err != nil {
		return fmt.Errorf("importing keys from Augur: %w", err)
	}

	logger.Info("keys imported from augur_operations.worker_oauth", "count", imported)
	return nil
}

// --- prioritize: push a repo to top of queue ---

func prioritizeCmd(cfgPath *string) *cobra.Command {
	return &cobra.Command{
		Use:   "prioritize [repo-url-or-id]",
		Short: "Push a repo to the top of the collection queue",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runPrioritize(*cfgPath, args[0])
		},
	}
}

func runPrioritize(cfgPath, target string) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	ctx := context.Background()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return err
	}
	defer store.Close()

	// Try parsing as a repo URL first, then look up the ID.
	parsed, parseErr := platform.ParseRepoURL(target)
	if parseErr == nil {
		// Look up repo_id by URL.
		repoID, err := store.UpsertRepo(ctx, &model.Repo{
			Platform: parsed.Platform,
			GitURL:   target,
			Name:     parsed.Repo,
			Owner:    parsed.Owner,
		})
		if err != nil {
			return err
		}
		if err := store.PrioritizeRepo(ctx, repoID); err != nil {
			return err
		}
		logger.Info("repo pushed to top of queue", "url", target, "repo_id", repoID)
		return nil
	}

	// Not a URL — error.
	return fmt.Errorf("could not parse %q as a repo URL: %w", target, parseErr)
}

// --- recollect: flag repos for full (since=zero) re-collection ---
//
// v0.18.24: two triggers set the `force_full_collect` flag on a repo's
// collection_queue row:
//
//   - Manual: `aveloxis recollect <url>...` — this command. One or more
//     URLs, each flipped to force_full_collect=TRUE. The flag is picked
//     up on the repo's next scheduled DequeueNext and determineSince
//     returns zero time for a full pass.
//   - Automatic: the scheduler flips the flag itself when a job ends
//     with a GraphQL-batch error class (see shouldForceFullRecollect in
//     internal/scheduler/scheduler.go).
//
// The flag is cleared by CompleteJob on the next successful collection.
// This command does NOT prioritize the repo — operators who want it
// sooner should also run `aveloxis prioritize <url>`.

func recollectCmd(cfgPath *string) *cobra.Command {
	return &cobra.Command{
		Use:   "recollect [repo-urls...]",
		Short: "Flag one or more repos for a full (since=zero) re-collection on their next scheduled cycle",
		Long: `Sets the force_full_collect flag on each named repo's collection_queue row.
The flag is picked up on the next scheduler cycle — the repo is re-collected
from the beginning of time (since=zero) instead of using the incremental
window, and the flag is cleared on successful completion.

Use this after a bug fix that invalidates a repo's collected data, or after
a GraphQL PR batch error that may have left some PR child data incomplete
(the scheduler auto-flags this case too).

This command does not change queue priority. Combine with 'aveloxis
prioritize <url>' if you want the repo collected immediately.`,
		Args: cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runRecollect(*cfgPath, args)
		},
	}
}

func runRecollect(cfgPath string, targets []string) error {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig(cfgPath, bootLog)
	logger := newLogger(cfg)

	ctx := context.Background()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
	if err != nil {
		return err
	}
	defer store.Close()

	var firstErr error
	for _, target := range targets {
		parsed, parseErr := platform.ParseRepoURL(target)
		if parseErr != nil {
			logger.Error("could not parse repo URL — skipping", "url", target, "error", parseErr)
			if firstErr == nil {
				firstErr = parseErr
			}
			continue
		}
		// UpsertRepo is idempotent; use it to resolve the URL to a
		// repo_id without requiring the caller to know the ID.
		repoID, err := store.UpsertRepo(ctx, &model.Repo{
			Platform: parsed.Platform,
			GitURL:   target,
			Name:     parsed.Repo,
			Owner:    parsed.Owner,
		})
		if err != nil {
			logger.Error("failed to resolve repo_id — skipping", "url", target, "error", err)
			if firstErr == nil {
				firstErr = err
			}
			continue
		}
		if err := store.SetForceFullCollect(ctx, repoID, true); err != nil {
			logger.Error("failed to set force_full_collect — skipping", "url", target, "repo_id", repoID, "error", err)
			if firstErr == nil {
				firstErr = err
			}
			continue
		}
		logger.Info("force_full_collect set — repo will be fully re-collected on next scheduler cycle",
			"url", target, "repo_id", repoID)
	}
	return firstErr
}

// --- migrate ---

func migrateCmd(cfgPath *string) *cobra.Command {
	var skipViews bool
	var noWait bool
	cmd := &cobra.Command{
		Use:   "migrate",
		Short: "Run database schema migrations",
		Long: `Runs the schema migrations and (by default) creates/refreshes
materialized views used by 8Knot and analytics.

Use --skip-views to skip the materialized view block entirely. This is
useful when you're iterating on a schema-error fix on a large database
where the matview rebuild adds significant time per attempt — run a
plain ` + "`aveloxis refresh-views`" + ` (or wait for the next scheduler
tick) once the schema errors are resolved.

Use --no-wait to fail fast if another aveloxis migration is already in
progress (rather than blocking on the advisory lock until the holder
releases). Useful in CI and ` + "`aveloxis stop all && aveloxis start all`" + `
flows where you want a clear error if a stale process is still
running migrations.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
			cfg := loadConfig(*cfgPath, bootLog)
			logger := newLogger(cfg)
			ctx := context.Background()
			store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionStringWithAppName("aveloxis-migrate"), logger)
			if err != nil {
				return err
			}
			defer store.Close()
			// The explicit migrate command always creates/refreshes views,
			// unless --skip-views is passed.
			store.SetMatviewSkip(skipViews)
			if !skipViews {
				store.SetMatviewOnStartup(true)
			}
			store.SetMigrateNoWait(noWait)
			return store.Migrate(ctx)
		},
	}
	cmd.Flags().BoolVar(&skipViews, "skip-views", false,
		"skip materialized view creation/refresh (run `aveloxis refresh-views` separately when ready)")
	cmd.Flags().BoolVar(&noWait, "no-wait", false,
		"fail fast if another aveloxis migration is in progress (don't block on the advisory lock)")
	return cmd
}

func refreshViewsCmd(cfgPath *string) *cobra.Command {
	return &cobra.Command{
		Use:   "refresh-views",
		Short: "Refresh all materialized views (for 8Knot/analytics)",
		Long:  `Refreshes all 18 materialized views used by 8Knot and other analytics tools. Views are also refreshed automatically every 2 hours by aveloxis serve.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
			cfg := loadConfig(*cfgPath, bootLog)
			logger := newLogger(cfg)
			ctx := context.Background()
			store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), logger)
			if err != nil {
				return err
			}
			defer store.Close()
			return db.RefreshMaterializedViews(ctx, store, logger)
		},
	}
}

func sbomCmd(cfgPath *string) *cobra.Command {
	var (
		format string
		output string
		store  bool
	)

	cmd := &cobra.Command{
		Use:   "sbom [repo-id]",
		Short: "Generate a Software Bill of Materials for a repository",
		Long: `Generates a CycloneDX or SPDX SBOM from the dependency data collected
for a repository. The repo must have been collected with dependency/libyear
analysis enabled (runs automatically during aveloxis serve).

Examples:
  aveloxis sbom 42                         # CycloneDX JSON to stdout
  aveloxis sbom 42 --format spdx           # SPDX JSON to stdout
  aveloxis sbom 42 -o sbom.json            # Write to file
  aveloxis sbom 42 --store                 # Store in repo_sbom_scans table`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
			cfg := loadConfig(*cfgPath, bootLog)

			repoID, err := strconv.ParseInt(args[0], 10, 64)
			if err != nil {
				return fmt.Errorf("invalid repo ID: %s", args[0])
			}

			ctx := context.Background()
			dbStore, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), bootLog)
			if err != nil {
				return err
			}
			defer dbStore.Close()

			sbomFormat := collector.FormatCycloneDX
			if format == "spdx" {
				sbomFormat = collector.FormatSPDX
			}

			data, err := collector.GenerateSBOM(ctx, dbStore, repoID, sbomFormat)
			if err != nil {
				return err
			}

			if store {
				if err := collector.StoreSBOM(ctx, dbStore, repoID, data); err != nil {
					return fmt.Errorf("storing SBOM: %w", err)
				}
				fmt.Fprintf(os.Stderr, "SBOM stored in repo_sbom_scans for repo_id %d\n", repoID)
			}

			if output != "" {
				if err := os.WriteFile(output, data, 0o644); err != nil {
					return err
				}
				fmt.Fprintf(os.Stderr, "SBOM written to %s\n", output)
			} else {
				fmt.Println(string(data))
			}
			return nil
		},
	}

	cmd.Flags().StringVar(&format, "format", "cyclonedx", "Output format: cyclonedx or spdx")
	cmd.Flags().StringVarP(&output, "output", "o", "", "Write to file instead of stdout")
	cmd.Flags().BoolVar(&store, "store", false, "Also store the SBOM in repo_sbom_scans")

	return cmd
}

func installToolsCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "install-tools",
		Short: "Install all optional analysis tools (scc, scorecard, scancode, etc.)",
		Long: `Installs all optional third-party tools used by Aveloxis collection phases.
Each tool is independently optional — if not installed, its phase is silently skipped.

Requires Go for scc/scorecard. Requires Python 3.10+ for scancode.

Tools installed:
  scc        — Code complexity analysis (repo_labor)
  scorecard  — OpenSSF Scorecard security checks (repo_deps_scorecard)
  scancode   — Per-file license/copyright detection (aveloxis_scan, every 30 days)`,
		RunE: func(cmd *cobra.Command, args []string) error {
			tools := collector.ExternalTools()
			installed := 0
			failed := 0

			for _, tool := range tools {
				// Check if already installed.
				if path, err := exec.LookPath(tool.CheckBinary); err == nil {
					fmt.Printf("✓ %s already installed: %s\n", tool.Name, path)
					installed++
					continue
				}

				fmt.Printf("Installing %s — %s...\n", tool.Name, tool.Description)

				if err := collector.RunToolInstall(tool); err != nil {
					fmt.Printf("✗ Failed to install %s: %v\n  Manual install: %s\n", tool.Name, err, tool.InstallCmd)
					failed++
					continue
				}

				// Verify it's on PATH.
				if path, err := exec.LookPath(tool.CheckBinary); err == nil {
					fmt.Printf("✓ %s installed: %s\n", tool.Name, path)
				} else {
					// Don't print generic PATH advice — the InstallFunc
					// already printed tool-specific guidance if needed.
					fmt.Printf("⚠ %s installed but not found on PATH.\n", tool.Name)
				}
				installed++
			}

			fmt.Printf("\n%d/%d tools installed", installed, len(tools))
			if failed > 0 {
				fmt.Printf(", %d failed", failed)
			}
			fmt.Println()
			return nil
		},
	}
}

func webCmd(cfgPath *string) *cobra.Command {
	return &cobra.Command{
		Use:   "web",
		Short: "Run the web GUI for group management (OAuth login)",
		Long: `Starts the web GUI where users can sign in with GitHub or GitLab,
create groups, and add repos or organizations to those groups.

Requires OAuth app credentials in aveloxis.json (web.github_client_id, etc.)
Create a GitHub OAuth app at: https://github.com/settings/developers
Create a GitLab OAuth app at: https://gitlab.com/-/profile/applications`,
		RunE: func(cmd *cobra.Command, args []string) error {
			bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
			cfg := loadConfig(*cfgPath, bootLog)
			logger := newLogger(cfg)

			webPidPath := pidfile.Path("web")
			pidfile.Write(webPidPath, os.Getpid())
			defer pidfile.Remove(webPidPath)

			ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
			defer cancel()

			store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionStringWithAppName("aveloxis-web"), logger)
			if err != nil {
				return err
			}
			defer store.Close()
			// NOTE: web does NOT run migrations. Use `aveloxis migrate` or
			// `aveloxis serve` for that. Running migrations from both serve
			// and web simultaneously causes conflicts.
			// Instead, CheckSchemaVersion warns if the DB is behind the binary.
			store.CheckSchemaVersion(ctx, logger)

			// Load GitHub keys for immediate org scanning (non-fatal for web — it
			// can still serve the GUI without keys, just can't scan orgs).
			ghKeys, _, _ := loadKeys(ctx, cfg, store, false, logger)

			webServer := web.New(store, cfg.Web, ghKeys, logger).
				WithMailer(mailer.New(mailer.Config{
					GmailUser:        cfg.Mail.GmailUser,
					GmailAppPassword: cfg.Mail.GmailAppPassword,
					FromName:         cfg.Mail.FromName,
					SiteURL:          cfg.Mail.SiteURL,
				}, logger))
			srv := &http.Server{Addr: cfg.Web.Addr, Handler: webServer.Handler()}

			go func() {
				logger.Info("web GUI listening", "addr", cfg.Web.Addr)
				if err := srv.ListenAndServe(); err != http.ErrServerClosed {
					logger.Error("web server error", "error", err)
				}
			}()

			<-ctx.Done()
			srv.Shutdown(context.Background())
			return nil
		},
	}
}

// validComponents lists the background-manageable process types.
var validComponents = []string{"serve", "web", "api"}

func startCmd(cfgPath *string) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "start [serve|web|api|all]",
		Short: "Start aveloxis components in the background",
		Long: `Launches the specified component(s) as background processes, writing
output to log files in ~/.aveloxis/:

  aveloxis start serve   → aveloxis.log   (scheduler + monitor)
  aveloxis start web     → web.log        (web GUI)
  aveloxis start api     → api.log        (REST API)
  aveloxis start all     → all three

PID files are written to ~/.aveloxis/aveloxis-{serve,web,api}.pid.
Use 'aveloxis stop' to shut them down gracefully.`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			target := strings.ToLower(args[0])

			var components []string
			if target == "all" {
				components = validComponents
			} else {
				if !slices.Contains(validComponents, target) {
					return fmt.Errorf("unknown component %q (use serve, web, api, or all)", target)
				}
				components = []string{target}
			}

			for _, comp := range components {
				if err := startComponent(comp, *cfgPath); err != nil {
					fmt.Printf("Failed to start %s: %v\n", comp, err)
				}
			}
			return nil
		},
	}
	return cmd
}

func startComponent(component, cfgPath string) error {
	// Check if already running.
	pidPath := pidfile.Path(component)
	if pid, err := pidfile.Read(pidPath); err == nil && pidfile.IsRunning(pid) {
		fmt.Printf("%s is already running (PID %d)\n", component, pid)
		return nil
	}

	logPath := pidfile.LogPath(component)
	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return fmt.Errorf("opening log file %s: %w", logPath, err)
	}

	// Build the command. Pass through the config path flag.
	execPath, err := os.Executable()
	if err != nil {
		logFile.Close()
		return fmt.Errorf("finding executable: %w", err)
	}

	cmdArgs := []string{component, "--config", cfgPath}
	proc := exec.Command(execPath, cmdArgs...)
	proc.Stdout = logFile
	proc.Stderr = logFile
	// Detach from the parent process group so it survives terminal close.
	proc.SysProcAttr = &syscall.SysProcAttr{Setsid: true}

	if err := proc.Start(); err != nil {
		logFile.Close()
		return fmt.Errorf("starting %s: %w", component, err)
	}

	pid := proc.Process.Pid
	if err := pidfile.Write(pidPath, pid); err != nil {
		fmt.Printf("Warning: started %s (PID %d) but failed to write PID file: %v\n", component, pid, err)
	}

	// Release the child — we don't wait for it.
	proc.Process.Release()
	logFile.Close()

	fmt.Printf("Started %s (PID %d), logging to %s\n", component, pid, logPath)
	return nil
}

// verifyBackendsDisconnected polls pg_stat_activity for backends with
// the given application_name (e.g., "aveloxis-serve") and waits up to
// 30 seconds for the count to drop to zero. If any persist, prints
// the persistent PIDs paired with a pg_terminate_backend recipe so
// the operator can act in seconds rather than wait the full TCP
// keepalive timeout (tens of minutes).
//
// v0.20.0 introduced this to close the gap that produced the
// 2026-05-08 26-minute orphan: SIGTERM was sent successfully, but the
// orphaned backend kept grinding a 26-minute UPDATE because the
// operator had no signal it was happening.
func verifyBackendsDisconnected(cfgPath, appName string) {
	bootLog := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelWarn}))
	cfg, err := config.Load(cfgPath)
	if err != nil {
		// No config means we can't check the DB. Operator gets the
		// SIGTERM result but no verification. Acceptable for `stop` to
		// degrade gracefully.
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
	defer cancel()
	store, err := db.NewPostgresStore(ctx, cfg.Database.ConnectionString(), bootLog)
	if err != nil {
		fmt.Printf("(could not verify %s backends disconnected: %v)\n", appName, err)
		return
	}
	defer store.Close()

	// Poll once a second for up to 30 seconds.
	deadline := time.Now().Add(30 * time.Second)
	var lastPids []int
	for time.Now().Before(deadline) {
		pids, err := store.PidsByAppName(ctx, appName)
		if err != nil {
			return
		}
		if len(pids) == 0 {
			return
		}
		lastPids = pids
		time.Sleep(1 * time.Second)
	}
	// Persistent backends after 30s — surface PIDs and the actionable fix.
	if len(lastPids) > 0 {
		fmt.Printf("WARNING: %d %s backend(s) did not disconnect within 30s after SIGTERM.\n",
			len(lastPids), appName)
		fmt.Printf("Persistent PIDs: %v\n", lastPids)
		fmt.Println("If you don't see a matching aveloxis process in `ps`, these are orphans.")
		fmt.Println("Terminate them with:")
		for _, pid := range lastPids {
			fmt.Printf("  SELECT pg_terminate_backend(%d);\n", pid)
		}
	}
}

func stopCmd(cfgPath *string) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "stop [serve|web|api|all]",
		Short: "Stop running aveloxis background processes",
		Long: `Sends SIGTERM to the specified component(s), triggering graceful shutdown.

  aveloxis stop serve   — stop the scheduler
  aveloxis stop web     — stop the web GUI
  aveloxis stop api     — stop the REST API
  aveloxis stop all     — stop all three
  aveloxis stop         — (no args) same as 'all'

Active workers finish their current API call, queue locks are released,
and any unprocessed staging data is preserved for the next startup.
PID files are cleaned up automatically.`,
		Args: cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			target := "all"
			if len(args) > 0 {
				target = strings.ToLower(args[0])
			}

			var components []string
			if target == "all" {
				components = validComponents
			} else {
				if !slices.Contains(validComponents, target) {
					return fmt.Errorf("unknown component %q (use serve, web, api, or all)", target)
				}
				components = []string{target}
			}

			stopped := 0
			for _, comp := range components {
				if ok := stopComponent(comp); ok {
					stopped++
					// v0.20.0: poll pg_stat_activity for the matching
					// application_name and warn if backends linger past
					// 30 seconds. Surfaces orphans-after-stop without
					// requiring the operator to know about pg_locks.
					verifyBackendsDisconnected(*cfgPath, "aveloxis-"+comp)
				}
			}
			if stopped == 0 {
				fmt.Println("No running aveloxis processes found.")
			}
			return nil
		},
	}
	return cmd
}

func stopComponent(component string) bool {
	// Strategy 1: PID file (preferred — reliable, written by start/serve/web/api).
	pidPath := pidfile.Path(component)
	if pid, err := pidfile.Read(pidPath); err == nil {
		if !pidfile.IsRunning(pid) {
			fmt.Printf("%s: stale PID file (PID %d not running), cleaning up\n", component, pid)
			pidfile.Remove(pidPath)
		} else if signalProcess(component, pid) {
			pidfile.Remove(pidPath)
			return true
		}
	}

	// Strategy 2: pgrep fallback — finds processes started before PID file support
	// was added, or started manually without 'aveloxis start'.
	out, err := exec.Command("pgrep", "-f", "aveloxis "+component).Output()
	if err != nil {
		return false
	}

	myPID := os.Getpid()
	stopped := false
	for field := range strings.FieldsSeq(strings.TrimSpace(string(out))) {
		pid, err := strconv.Atoi(field)
		if err != nil || pid == myPID {
			continue
		}
		if signalProcess(component, pid) {
			stopped = true
		}
	}
	return stopped
}

func signalProcess(component string, pid int) bool {
	proc, err := os.FindProcess(pid)
	if err != nil {
		return false
	}
	if err := proc.Signal(syscall.SIGTERM); err != nil {
		fmt.Printf("Failed to stop %s (PID %d): %v\n", component, pid, err)
		return false
	}
	fmt.Printf("Stopped %s (PID %d)\n", component, pid)
	return true
}

func versionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "Print version information",
		Run:   func(cmd *cobra.Command, args []string) { fmt.Println("aveloxis v" + Version) },
	}
}

// --- helpers ---

func loadConfig(cfgPath string, logger *slog.Logger) *config.Config {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		logger.Warn("config file not found, using defaults", "path", cfgPath, "error", err)
		cfg = config.DefaultConfig()
	}
	return cfg
}

// newLogger creates a logger from the config's log_level setting.
func newLogger(cfg *config.Config) *slog.Logger {
	return slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: cfg.SlogLevel()}))
}

// loadKeys builds key pools. Priority order:
//  1. aveloxis_ops.worker_oauth (always checked)
//  2. augur_operations.worker_oauth (if --augur-keys is set)
//  3. JSON config file (lowest priority, for standalone deployments)
func loadKeys(ctx context.Context, cfg *config.Config, store *db.PostgresStore, useAugurKeys bool, logger *slog.Logger) (*platform.KeyPool, *platform.KeyPool, error) {
	ghTokens := cfg.GitHub.APIKeys
	glTokens := cfg.GitLab.APIKeys

	// Load from database (aveloxis_ops first, augur_operations as fallback).
	if dbGH, err := db.LoadAPIKeys(ctx, store.Pool(), "github", useAugurKeys); err != nil {
		logger.Error("failed to load GitHub API keys from database", "error", err)
	} else if len(dbGH) > 0 {
		logger.Info("loaded GitHub keys from database", "count", len(dbGH))
		ghTokens = append(ghTokens, dbGH...)
	}
	if dbGL, err := db.LoadAPIKeys(ctx, store.Pool(), "gitlab", useAugurKeys); err != nil {
		logger.Error("failed to load GitLab API keys from database", "error", err)
	} else if len(dbGL) > 0 {
		logger.Info("loaded GitLab keys from database", "count", len(dbGL))
		glTokens = append(glTokens, dbGL...)
	}

	if len(ghTokens) == 0 && len(glTokens) == 0 {
		return nil, nil, fmt.Errorf("no API keys configured for any platform — add keys via 'aveloxis add-key <token> --platform github' or store them in the database. Collection is impossible without API keys")
	}
	if len(ghTokens) == 0 {
		logger.Warn("no GitHub API keys configured — GitHub repos will not be collected")
	}
	if len(glTokens) == 0 {
		logger.Warn("no GitLab API keys configured — GitLab repos will not be collected")
	}

	return platform.NewKeyPool(ghTokens, logger), platform.NewKeyPool(glTokens, logger), nil
}
