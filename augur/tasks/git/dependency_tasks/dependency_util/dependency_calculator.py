from augur.tasks.git.dependency_tasks.dependency_util import python_deps
from augur.tasks.git.dependency_tasks.dependency_util import ruby_deps
from augur.tasks.git.dependency_tasks.dependency_util import php_deps
from augur.tasks.git.dependency_tasks.dependency_util import javascript_deps
from augur.tasks.git.dependency_tasks.dependency_util import vb_deps
from augur.tasks.git.dependency_tasks.dependency_util import csharp_deps
from augur.tasks.git.dependency_tasks.dependency_util import java_deps
from augur.tasks.git.dependency_tasks.dependency_util import cpp_deps
from augur.tasks.git.dependency_tasks.dependency_util import c_deps
from augur.tasks.git.dependency_tasks.dependency_util import go_deps
from augur.tasks.git.dependency_tasks.dependency_util import kotlin_deps
from augur.tasks.git.dependency_tasks.dependency_util import rust_deps
from augur.tasks.git.dependency_tasks.dependency_util import r_deps
from augur.tasks.git.dependency_tasks.dependency_util import dependency_calculator

#Returns generator iterable to tuples of modules and their names
def get_dependency_analysis_module_tuples():
	yield python_deps, 'python'
	yield ruby_deps, 'ruby'
	yield php_deps, 'php'
	yield javascript_deps, 'javascript'
	yield vb_deps, 'visual basic'
	yield csharp_deps, 'C#'
	yield java_deps, 'java'
	yield cpp_deps, 'C++'
	yield c_deps, 'C'
	yield go_deps, 'go'
	yield kotlin_deps, 'kotlin'
	yield rust_deps, 'rust'
	yield r_deps, 'R'

class Dep:
	def __init__(self, name, language, count):
		self.name = name
		self.language = language
		self.count = count
	def __repr__(self):
		return f'Dep(name={self.name}, language={self.language}, count={self.count})'

def get_deps(path,logger):
	deps = []

	#Iterate through modules for each language to apply them to the path for the repo.
	for lib_module, name in get_dependency_analysis_module_tuples():
		deps.extend(get_language_deps(path, lib_module, name,logger))

	return deps
	
def get_language_deps(path, language, name,logger):
	files = language.get_files(path)
	deps_map = {}
	for f in files:
		try:
			f_deps = language.get_deps_for_file(f)
		except UnicodeDecodeError as e:
			logger.error(f"Could not parse file {f} at path: {path}\n Error: {e}")
			return []
		except IsADirectoryError as e:
			logger.error(f"Given file's path is a directory!\n file: {f}\n path: {path}\n Error: {e}")
			return []
		except FileNotFoundError as e:
			logger.error(f"Given file not found!\n file: {f}\n path: {path}\n Error: {e}")
			return []

		if f_deps is None:
			continue
		for dep in f_deps:
			if dep in deps_map:
				deps_map[dep].count += 1
			else:
				deps_map[dep] = Dep(dep, name, 1)
	return list(deps_map.values())
