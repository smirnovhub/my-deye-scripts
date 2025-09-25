import os
import re
import subprocess

from typing import Dict, List, Tuple
from collections import defaultdict
from subprocess import CompletedProcess

from telebot_git_exception import TelebotGitException
from telebot_git_exception import TelebotGitException

def check_git_result_and_raise(result: CompletedProcess):
  if result.returncode == 0:
    return

  stderr = result.stderr.lower()
  if 'no stash entries found' in stderr:
    return

  if 'conflict' in stderr or 'would be overwritten' in stderr:
    raise TelebotGitException('local changes conflict with remote changes')

  if 'fatal:' in stderr:
    index = stderr.find('fatal:') + len('fatal:')
    newline_index = stderr.find('\n', index)

    if newline_index != -1:
      error_text = result.stderr[index:newline_index].strip()
    else:
      error_text = result.stderr[index:].strip()

    raise TelebotGitException(error_text)

  raise TelebotGitException('git returned a non-zero exit code')

def is_repository_up_to_date() -> bool:
  """
  Check if the local repository is up to date with the remote.

  This runs `git remote show origin` and searches for the phrase 'up to date'
  in the output.

  Returns:
      bool: True if the repository is synchronized, False otherwise.

  Raises:
      TelebotGitException: If the git command fails.
  """
  try:
    current_dir = os.path.dirname(__file__)
    # Run 'git remote show origin' to get information about remote branches
    result = subprocess.run(
      ["git", "-C", current_dir, "remote", "show", "origin"],
      capture_output = True,
      text = True,
    )

    check_git_result_and_raise(result)
    # If 'up to date' appears in the output, the local branch is synchronized
    return 'up to date' in result.stdout.lower()
  except Exception as e:
    raise TelebotGitException(f'git remote show origin failed: {str(e)}')

def stash_push():
  current_dir = os.path.dirname(__file__)
  try:
    # Stash all changes
    result = subprocess.run(
      ['git', '-C', current_dir, 'stash', 'push'],
      capture_output = True,
      text = True,
    )
    check_git_result_and_raise(result)
  except TelebotGitException as e:
    raise TelebotGitException(f'git stash push failed: {str(e)}')
  except Exception as e:
    raise TelebotGitException(f'git stash push failed: {str(e)}')

def stash_pop():
  current_dir = os.path.dirname(__file__)
  try:
    # Stash all changes
    result = subprocess.run(
      ['git', '-C', current_dir, 'stash', 'pop'],
      capture_output = True,
      text = True,
    )
    check_git_result_and_raise(result)
  except TelebotGitException as e:
    raise TelebotGitException(f'git stash pop failed: {str(e)}')
  except Exception as e:
    raise TelebotGitException(f'git stash pop failed: {str(e)}')

def revert_to_revision(commit_hash: str) -> str:
  current_dir = os.path.dirname(__file__)
  try:
    result = subprocess.run(
      ['git', '-C', current_dir, 'reset', '--hard', commit_hash],
      capture_output = True,
      text = True,
    )
    check_git_result_and_raise(result)
    return result.stdout
  except TelebotGitException as e:
    raise TelebotGitException(f'git reset --hard failed: {str(e)}')
  except Exception as e:
    raise TelebotGitException(f'git reset --hard failed: {str(e)}')

def get_last_commit_hash() -> str:
  current_dir = os.path.dirname(__file__)
  return _run_git_command_and_get_result(
    ["git", "-C", current_dir, "rev-parse", "HEAD"],
    'rev-parse HEAD',
  )

def get_last_commit_hash_and_comment() -> str:
  current_dir = os.path.dirname(__file__)

  last_commit = _run_git_command_and_get_result(
    ["git", "-C", current_dir, "log", "-1", "--pretty=format:%h %ad %s", "--date=short"],
    'rev-parse HEAD',
  )

  match = re.search(r"(.*)Merge pull request #(\d+)", last_commit)
  if match:
    last_commit = f"{match.group(1)}PR #{match.group(2)}"

  return last_commit

def _run_git_command_and_get_result(commands: List[str], command_name: str) -> str:
  """
  Execute a git command and return its stdout output as a string.

  Args:
      commands (List[str]): The command and its arguments to execute as a list of strings
      command_name (str): A short name or description of the command, used in error messages

  Returns:
      str: The standard output of the executed command, stripped of leading/trailing whitespace.

  Raises:
      TelebotGitException: If the command fails for any reason, including:
          - A non-zero exit code detected
          - Any other unexpected exception
  """
  try:
    result = subprocess.run(
      commands,
      capture_output = True,
      text = True,
    )
    check_git_result_and_raise(result)
    return result.stdout.strip()
  except TelebotGitException as e:
    raise TelebotGitException(f'git {command_name} failed: {str(e)}')
  except Exception as e:
    raise TelebotGitException(f'git {command_name} failed: {str(e)}')

def get_last_commits(pr_max_count: int = 5, regular_commits_max_count = 10) -> Dict[str, str]:
  """
  Get all merge commits of the format "Merge pull request #<number>" in the local repository.
  If no merge commits are found, return the last `max_count` commits.
  If commit messages are duplicated, append a suffix "-1", "-2", etc. to all duplicates (including the first)
  to make keys unique.

  Returns:
      dict[str, str]: Dictionary where key is "YYYY-MM-DD <message>-N" and value is the commit hash.

  Raises:
      TelebotGitException: If the git command fails.
  """
  commits_dict: Dict[str, str] = {}
  current_dir = os.path.dirname(__file__)

  try:
    # Try to get only merge commits with date
    max_count = pr_max_count
    result = subprocess.run(
      [
        "git",
        "-C",
        current_dir,
        "log",
        f"-n{max_count}",
        "--grep=Merge pull request #[0-9]+",
        "-E",
        "--pretty=format:%H %ad %s",
        "--date=short",
      ],
      capture_output = True,
      text = True,
    )
    check_git_result_and_raise(result)
    lines = result.stdout.strip().split('\n')

    # If no merge commits are found, get the last `max_count` commits with date
    if not lines or lines == ['']:
      max_count = regular_commits_max_count
      result = subprocess.run(
        [
          "git",
          "-C",
          current_dir,
          "log",
          f"-n{max_count}",
          "--pretty=format:%H %ad %s",
          "--date=short",
        ],
        capture_output = True,
        text = True,
      )
      check_git_result_and_raise(result)
      lines = result.stdout.strip().split('\n')

    # First, collect all base keys and their hashes
    base_keys: List[Tuple[str, str]] = []
    for i, line in enumerate(lines):
      if i > max_count:
        break
      if not line:
        continue
      parts = line.split(' ', 2)
      if len(parts) < 3:
        continue
      commit_hash, date, message = parts

      match = re.search(r"Merge pull request #(\d+)", message)
      if match:
        message = f"PR #{match.group(1)}"

      base_key = f"{date} {message}"
      base_keys.append((base_key, commit_hash))

    # Count occurrences of each base key
    counts = defaultdict(int)
    for base_key, commit_hash in base_keys:
      counts[base_key] += 1

    # Assign keys with suffixes for duplicates
    seen = defaultdict(int)
    for base_key, commit_hash in base_keys:
      if counts[base_key] > 1:
        seen[base_key] += 1
        key = f"{base_key}-{seen[base_key]}"
      else:
        key = base_key
      commits_dict[key] = commit_hash

  except Exception:
    return commits_dict

  return commits_dict
