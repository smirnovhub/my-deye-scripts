import os
import re
import asyncio

from typing import Dict, List, Optional, Tuple

from deye_exceptions import DeyeValueException
from git_exceptions import GitException

class GitHelperAsync:
  def __init__(self):
    self._current_dir = os.path.dirname(__file__)
    self._local_repo_mark = 'git.dmitry'

  async def is_repository_up_to_date(self) -> bool:
    """
    Check if the local repository is up to date with the remote.

    This runs `git remote show origin` and searches for the phrase 'up to date'
    in the output.

    Returns:
        bool: True if the repository is synchronized, False otherwise.

    Raises:
        GitException: If the git command fails.
    """
    # Run 'git remote show origin' to get information about remote branches
    result = await self._run_git_command_and_get_result_async(
      ["remote", "show", "origin"],
      'remote show origin',
    )
    return 'up to date' in result.lower()

  async def stash_push(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ['stash', 'push'],
      'stash push',
    )

  async def stash_pop(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ['stash', 'pop'],
      'stash pop',
    )

  async def stash_clear(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ['stash', 'clear'],
      'stash clear',
    )

  async def pull(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ["pull"],
      'pull',
    )

  async def submodule_update(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ["submodule", "update", "--init", "--recursive"],
      'submodule update',
    )

  async def revert_to_revision(self, commit_hash: str) -> str:
    return await self._run_git_command_and_get_result_async(
      ['reset', '--hard', commit_hash],
      'reset --hard',
    )

  async def get_current_branch_name(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ["rev-parse", "--abbrev-ref", "HEAD"],
      'rev-parse --abbrev-ref HEAD',
    )

  async def get_last_commit_hash(self) -> str:
    repo_name = await self.get_repo_name()

    # Return global last commit hash for production repo
    if self._local_repo_mark not in repo_name:
      return await self._run_git_command_and_get_result_async(
        ["rev-parse", "HEAD"],
        'rev-parse HEAD',
      )

    # Return last commit hash for top-level folder in working repo

    # Find the root of the Git repository
    # This command returns the absolute path to the folder containing the .git directory
    repo_root = await self._run_git_command_and_get_result_async(
      ['rev-parse', '--show-toplevel'],
      'rev-parse --show-toplevel',
      cwd = self._current_dir,
    )

    # Calculate the relative path from the repo root to the script's directory
    # Example: if root is '/projects/app' and script is in '/projects/app/src/utils'
    # the relative path will be 'src/utils'
    rel_path = os.path.relpath(self._current_dir, repo_root)

    # Extract the top-level directory name from the relative path
    # Using os.sep ensures it works on both Windows and Linux
    top_folder_name = rel_path.split(os.sep)[0]

    # Handle the edge case where the script is executed directly from the repo root
    if top_folder_name == ".":
      target_path = repo_root
    else:
      # Reconstruct the full path to that top-level folder
      target_path = os.path.join(repo_root, top_folder_name)

    # Get the hash of the latest commit that affected this specific folder
    # 'rev-list -1 HEAD -- <path>' returns the most recent commit ID for the given path
    return await self._run_git_command_and_get_result_async(
      ['rev-list', '-1', 'HEAD', '--', target_path],
      'rev-list -1 HEAD',
      cwd = repo_root,
    )

  async def get_repo_name(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ["config", "--get", "remote.origin.url"],
      'config --get remote.origin.url',
    )

  async def get_last_commit_short_hash(self) -> str:
    return await self._run_git_command_and_get_result_async(
      ["rev-parse", "--short", "HEAD"],
      'rev-parse --short HEAD',
    )

  async def get_last_commit_hash_and_comment(self) -> str:
    last_commit = await self._run_git_command_and_get_result_async(
      ["log", "-1", "--pretty=format:%h %ad %s", "--date=short"],
      'log -1',
    )

    match = re.search(r"(.*)Merge pull request #(\d+)", last_commit)
    if match:
      last_commit = f"{match.group(1)}PR #{match.group(2)}"

    return last_commit

  async def get_last_commits(self, pr_max_count: int = 5, regular_commits_max_count = 25) -> Dict[str, str]:
    """
    Get all merge commits of the format "Merge pull request #<number>" in the local repository.
    If no merge commits are found, return the last `max_count` commits.
    If commit messages are duplicated, append a suffix "-1", "-2", etc. to all duplicates (including the first)
    to make keys unique.

    Returns:
        dict[str, str]: Dictionary where key is "YYYY-MM-DD <message>-N" and value is the commit hash.

    Raises:
        GitException: If the git command fails
        DeyeValueException: If other exception occurred
    """
    commits_dict: Dict[str, str] = {}
    try:
      # Try to get only merge commits with date
      max_count = pr_max_count
      result = await self._run_git_command_and_get_result_async(
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
        result = await self._run_git_command_and_get_result_async(
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

  async def _run_git_command_and_get_result_async(
    self,
    commands: List[str],
    command_name: str,
    cwd: Optional[str] = None,
  ) -> str:
    try:
      # Create subprocess asynchronously
      process = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        self._current_dir,
        *commands,
        cwd = cwd,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE,
      )

      # Wait for process completion and capture output
      stdout_bytes, stderr_bytes = await process.communicate()
      await process.wait()

      # Decode output to text
      stdout = stdout_bytes.decode().strip() if stdout_bytes else ""
      stderr = stderr_bytes.decode().strip() if stderr_bytes else ""

      self._check_git_result_and_raise(
        returncode = process.returncode,
        stdout = stdout,
        stderr = stderr,
      )

      return stdout

    except GitException as e:
      raise GitException(f'git {command_name} failed: {str(e)}')
    except Exception as e:
      raise GitException(f'git {command_name} failed: {str(e)}')

  def _check_git_result_and_raise(
    self,
    returncode: Optional[int],
    stdout: str,
    stderr: str,
  ):
    # Handle the case where the process didn't return a code (safety check)
    if returncode is None:
      raise GitException("Process did not exit correctly (no return code)")

    if returncode == 0:
      return

    stdout = stdout.lower()
    stderr = stderr.lower()
    output = stdout + stderr

    if 'no stash entries found' in output:
      return

    if 'conflict' in output or 'would be overwritten' in output:
      raise GitException('local changes conflict with remote changes')

    if 'fatal:' in stderr:
      index = stderr.find('fatal:') + len('fatal:')
      newline_index = stderr.find('\n', index)

      if newline_index != -1:
        error_text = stderr[index:newline_index].strip()
      else:
        error_text = stderr[index:].strip()

      raise GitException(error_text)

    raise GitException(output)
