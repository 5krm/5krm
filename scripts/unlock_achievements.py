"""
GitHub Achievement Unlocker
============================
Automates actions to unlock official GitHub profile achievements:
- Quickdraw (⚡) : Close an issue/PR within 5 minutes of opening
- YOLO (😎)      : Merge a PR without code review
- Pair Extraordinaire (👯) : Merge a PR with a co-authored commit
- Pull Shark (🦈) : Open and merge PRs (Bronze: 2, Silver: 16)
"""

import sys
import time
import requests

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def unlock_achievements(token: str, username: str, repo: str, pull_shark_count: int = 2):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-Achievement-Unlocker"
    }
    api_url = f"https://api.github.com/repos/{username}/{repo}"

    # Verify repository access
    print_header("1. Checking Repository Access")
    r = requests.get(api_url, headers=headers)
    if r.status_code != 200:
        print(f"[-] Error accessing {username}/{repo}: {r.status_code} - {r.text}")
        return False
    repo_data = r.json()
    default_branch = repo_data.get("default_branch", "main")
    print(f"[+] Connected to {repo_data['full_name']} (Default branch: {default_branch})")

    # 1. Quickdraw: Open and immediately close an issue
    print_header("2. Unlocking 'Quickdraw' (⚡)")
    print("[*] Creating an issue...")
    issue_resp = requests.post(f"{api_url}/issues", headers=headers, json={
        "title": "Speed Test - Quickdraw Badge",
        "body": "Unlocking Quickdraw achievement by closing immediately."
    })
    if issue_resp.status_code == 201:
        issue_number = issue_resp.json()["number"]
        print(f"[+] Issue #{issue_number} created.")
        time.sleep(1)
        close_resp = requests.patch(f"{api_url}/issues/{issue_number}", headers=headers, json={
            "state": "closed"
        })
        if close_resp.status_code == 200:
            print("[+] Issue closed within seconds! -> 'Quickdraw' Unlocked!")
        else:
            print(f"[-] Failed to close issue: {close_resp.text}")
    else:
        print(f"[-] Failed to create issue: {issue_resp.text}")

    # Get default branch commit SHA
    ref_resp = requests.get(f"{api_url}/git/ref/heads/{default_branch}", headers=headers)
    if ref_resp.status_code != 200:
        print(f"[-] Failed to get head SHA of {default_branch}: {ref_resp.text}")
        return False
    base_sha = ref_resp.json()["object"]["sha"]

    # 2. Pair Extraordinaire & YOLO: PR with Co-authored commit
    print_header("3. Unlocking 'Pair Extraordinaire' (👯) & 'YOLO' (😎)")
    branch_name = f"achievement-unlock-pair-{int(time.time())}"
    
    # Create branch
    requests.post(f"{api_url}/git/refs", headers=headers, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    })

    # Create file with co-authored commit
    commit_msg = (
        "Add pair programming achievement\n\n"
        "Co-authored-by: octocat <octocat@github.com>"
    )
    import base64
    file_content = base64.b64encode(b"# Achievement Unlocker\nUnlocked with co-author!\n").decode("utf-8")
    requests.put(f"{api_url}/contents/achievement_badge.md", headers=headers, json={
        "message": commit_msg,
        "content": file_content,
        "branch": branch_name
    })

    # Open PR
    pr_resp = requests.post(f"{api_url}/pulls", headers=headers, json={
        "title": "Pair Extraordinaire & YOLO badge trigger",
        "head": branch_name,
        "base": default_branch,
        "body": "Merged without review and co-authored."
    })

    if pr_resp.status_code == 201:
        pr_number = pr_resp.json()["number"]
        print(f"[+] Pull Request #{pr_number} created.")
        # Merge PR immediately without review (YOLO & Pair Extraordinaire)
        merge_resp = requests.put(f"{api_url}/pulls/{pr_number}/merge", headers=headers, json={
            "commit_title": "Merge PR for Pair Extraordinaire and YOLO",
            "merge_method": "squash"
        })
        if merge_resp.status_code == 200:
            print("[+] PR Merged! -> 'Pair Extraordinaire' & 'YOLO' Unlocked!")
        else:
            print(f"[-] Failed to merge PR: {merge_resp.text}")
    else:
        print(f"[-] Failed to create PR: {pr_resp.text}")

    # 3. Pull Shark: Merge PRs
    print_header(f"4. Unlocking 'Pull Shark' (🦈) (Merging {pull_shark_count} PRs)")
    for i in range(1, pull_shark_count + 1):
        ts = int(time.time()) + i
        bname = f"pull-shark-branch-{ts}"
        
        # Get latest default branch sha
        ref = requests.get(f"{api_url}/git/ref/heads/{default_branch}", headers=headers).json()
        current_sha = ref["object"]["sha"]
        
        requests.post(f"{api_url}/git/refs", headers=headers, json={
            "ref": f"refs/heads/{bname}",
            "sha": current_sha
        })

        content_str = base64.b64encode(f"Pull shark step {i}\n".encode("utf-8")).decode("utf-8")
        requests.put(f"{api_url}/contents/pull_shark_{i}.txt", headers=headers, json={
            "message": f"Pull Shark commit {i}",
            "content": content_str,
            "branch": bname
        })

        pr = requests.post(f"{api_url}/pulls", headers=headers, json={
            "title": f"Pull Shark iteration {i}",
            "head": bname,
            "base": default_branch,
            "body": f"Automated PR #{i} for Pull Shark badge."
        }).json()

        if "number" in pr:
            requests.put(f"{api_url}/pulls/{pr['number']}/merge", headers=headers, json={
                "commit_title": f"Merge Pull Shark #{i}",
                "merge_method": "squash"
            })
            print(f"[+] Pull Shark iteration {i}/{pull_shark_count} completed.")
        time.sleep(1)

    print("\n[✔] Done! GitHub will calculate and show your badges in your profile within 5-15 minutes.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python unlock_achievements.py <GITHUB_TOKEN> <USERNAME> <REPO_NAME> [PULL_SHARK_COUNT]")
        print("Example:")
        print("  python unlock_achievements.py ghp_xxx 5krm 5krm 2")
        sys.exit(1)

    token = sys.argv[1]
    user = sys.argv[2]
    repo = sys.argv[3]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 2

    unlock_achievements(token, user, repo, count)
