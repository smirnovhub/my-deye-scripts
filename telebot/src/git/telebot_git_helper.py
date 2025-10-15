import os
import re
import subprocess

from typing import Dict, List, Tuple
from subprocess import CompletedProcess

from deye_exceptions import DeyeValueException
from telebot_git_exception import TelebotGitException

class TelebotGitHelper:
  def __init__(self):
    self._current_dir = os.path.dirname(__file__)

  def is_repository_up_to_date(self) -> bool:
    """
    Check if the local repository is up to date with the remote.

    This runs `git remote show origin` and searches for the phrase 'up to date'
    in the output.

    Returns:
        bool: True if the repository is synchronized, False otherwise.

    Raises:
        TelebotGitException: If the git command fails.
    """
    # Run 'git remote show origin' to get information about remote branches
    result = self._run_git_command_and_get_result(
      ["remote", "show", "origin"],
      'remote show origin',
    )
    return 'up to date' in result.lower()

  def stash_push(self) -> str:
    return self._run_git_command_and_get_result(
      ['stash', 'push'],
      'stash push',
    )

  def stash_pop(self) -> str:
    return self._run_git_command_and_get_result(
      ['stash', 'pop'],
      'stash pop',
    )

  def stash_clear(self) -> str:
    return self._run_git_command_and_get_result(
      ['stash', 'clear'],
      'stash clear',
    )

  def pull(self) -> str:
    return self._run_git_command_and_get_result(
      ["pull"],
      'pull',
    )

  def revert_to_revision(self, commit_hash: str) -> str:
    return self._run_git_command_and_get_result(
      ['reset', '--hard', commit_hash],
      'reset --hard',
    )

  def get_current_branch_name(self) -> str:
    return self._run_git_command_and_get_result(
      ["rev-parse", "--abbrev-ref", "HEAD"],
      'rev-parse --abbrev-ref HEAD',
    )

  def get_last_commit_hash(self) -> str:
    return self._run_git_command_and_get_result(
      ["rev-parse", "HEAD"],
      'rev-parse HEAD',
    )

  def get_last_commit_short_hash(self) -> str:
    return self._run_git_command_and_get_result(
      ["rev-parse", "--short", "HEAD"],
      'rev-parse --short HEAD',
    )

  def get_last_commit_hash_and_comment(self) -> str:
    last_commit = self._run_git_command_and_get_result(
      ["log", "-1", "--pretty=format:%h %ad %s", "--date=short"],
      'log -1',
    )

    match = re.search(r"(.*)Merge pull request #(\d+)", last_commit)
    if match:
      last_commit = f"{match.group(1)}PR #{match.group(2)}"

    return last_commit

  def get_last_commits(self, pr_max_count: int = 5, regular_commits_max_count = 10) -> Dict[str, str]:
    """
    Get all merge commits of the format "Merge pull request #<number>" in the local repository.
    If no merge commits are found, return the last `max_count` commits.
    If commit messages are duplicated, append a suffix "-1", "-2", etc. to all duplicates (including the first)
    to make keys unique.

    Returns:
        dict[str, str]: Dictionary where key is "YYYY-MM-DD <message>-N" and value is the commit hash.

    Raises:
        TelebotGitException: If the git command fails
        DeyeValueException: If other exception occurred
    """
    commits_dict: Dict[str, str] = {}
    try:
      # Try to get only merge commits with date
      max_count = pr_max_count
      result = self._run_git_command_and_get_result(
        [
          "log",
          f"-n{max_count}",
          "--grep=Merge pull request #[0-9]+",
          "-E",
          "--pretty=format:%H %ad %s",
          "--date=short",
        ],
        'log -n --grep -E',
      )

      lines = result.strip().split('\n')

      # If no merge commits are found, get the last `max_count` commits with date
      if not lines or lines == ['']:
        max_count = regular_commits_max_count
        result = self._run_git_command_and_get_result(
          [
            "log",
            f"-n{max_count}",
            "--pretty=format:%H %ad %s",
            "--date=short",
          ],
          'log -n',
        )

        lines = result.strip().split('\n')

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
      counts: Dict[str, int] = {}
      for base_key, commit_hash in base_keys:
        counts[base_key] = counts.get(base_key, 0) + 1

      # Assign keys with suffixes for duplicates
      seen: Dict[str, int] = {}
      for base_key, commit_hash in base_keys:
        if counts[base_key] > 1:
          seen[base_key] = seen.get(base_key, 0) + 1
          key = f"{base_key}-{seen[base_key]}"
        else:
          key = base_key
        commits_dict[key] = commit_hash

    except Exception as e:
      raise DeyeValueException(f'{e.__class__.__name__}: {str(e)}')

    return commits_dict

  def _run_git_command_and_get_result(self, commands: List[str], command_name: str) -> str:
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
        ["git", "-C", self._current_dir] + commands,
        capture_output = True,
        text = True,
      )
      self._check_git_result_and_raise(result)
      return result.stdout.strip()
    except TelebotGitException as e:
      raise TelebotGitException(f'git {command_name} failed: {str(e)}')
    except Exception as e:
      raise TelebotGitException(f'git {command_name} failed: {str(e)}')

  def _check_git_result_and_raise(self, result: CompletedProcess):
    if result.returncode == 0:
      return

    stdout = result.stdout.lower()
    stderr = result.stderr.lower()
    output = stdout + stderr

    if 'no stash entries found' in output:
      return

    if 'conflict' in output or 'would be overwritten' in output:
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
