package main

import (
	"reflect"
	"slices"
	"testing"

	"github.com/aveloxis/aveloxis/internal/model"
)

func TestIsOrgURL(t *testing.T) {
	tests := []struct {
		name     string
		rawURL   string
		wantOK   bool
		wantHost string
		wantOrg  string
		wantPlat model.Platform
	}{
		{
			name:     "github org URL",
			rawURL:   "https://github.com/chaoss",
			wantOK:   true,
			wantHost: "github.com",
			wantOrg:  "chaoss",
			wantPlat: model.PlatformGitHub,
		},
		{
			name:     "github org URL with trailing slash and spaces",
			rawURL:   "  https://github.com/augurlabs/  ",
			wantOK:   true,
			wantHost: "github.com",
			wantOrg:  "augurlabs",
			wantPlat: model.PlatformGitHub,
		},
		{
			name:   "github repo URL is not treated as org",
			rawURL: "https://github.com/chaoss/augur",
		},
		{
			name:   "gitlab group currently not handled by isOrgURL",
			rawURL: "https://gitlab.com/group",
		},
		{
			name:   "invalid URL",
			rawURL: "://bad",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotOK, gotHost, gotOrg, gotPlat := isOrgURL(tt.rawURL)
			if gotOK != tt.wantOK || gotHost != tt.wantHost || gotOrg != tt.wantOrg || gotPlat != tt.wantPlat {
				t.Fatalf("isOrgURL(%q) = (%v, %q, %q, %v), want (%v, %q, %q, %v)",
					tt.rawURL, gotOK, gotHost, gotOrg, gotPlat,
					tt.wantOK, tt.wantHost, tt.wantOrg, tt.wantPlat)
			}
		})
	}
}

func TestGroupDisplayName(t *testing.T) {
	tests := []struct {
		name       string
		foundation string
		status     string
		want       string
	}{
		{name: "cncf uppercase special-case", foundation: "cncf", status: "graduated", want: "CNCF Graduated"},
		{name: "apache title-case", foundation: "apache", status: "incubating", want: "Apache Incubating"},
		{name: "generic title-case", foundation: "linux", status: "sandbox", want: "Linux Sandbox"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := groupDisplayName(tt.foundation, tt.status); got != tt.want {
				t.Fatalf("groupDisplayName(%q, %q) = %q, want %q", tt.foundation, tt.status, got, tt.want)
			}
		})
	}
}

func TestOrderedKeys(t *testing.T) {
	tallies := map[string]*foundationTally{
		"apache:incubating": {repos: 1},
		"cncf:sandbox":      {repos: 1},
		"cncf:graduated":    {repos: 1},
		"custom:beta":       {repos: 1},
	}
	got := orderedKeys(tallies)

	wantPrefix := []string{"cncf:graduated", "cncf:sandbox", "apache:incubating"}
	if len(got) < len(wantPrefix) {
		t.Fatalf("orderedKeys returned too few keys: got %v", got)
	}
	if !reflect.DeepEqual(got[:len(wantPrefix)], wantPrefix) {
		t.Fatalf("orderedKeys prefix = %v, want %v", got[:len(wantPrefix)], wantPrefix)
	}

	if !slices.Contains(got, "custom:beta") {
		t.Fatalf("orderedKeys should include unknown key: got %v", got)
	}
}

func TestCountMissing(t *testing.T) {
	a := map[string]struct{}{"1": {}, "2": {}, "3": {}}
	b := map[string]struct{}{"2": {}, "4": {}}
	if got := countMissing(a, b); got != 2 {
		t.Fatalf("countMissing returned %d, want 2", got)
	}

	if got := countMissing(map[string]struct{}{}, b); got != 0 {
		t.Fatalf("countMissing(empty, b) returned %d, want 0", got)
	}
}
