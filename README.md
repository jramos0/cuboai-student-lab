# CuboAI — Beyond Vibe Coding (Student Lab)

This is an intentionally flawed **local-only** training application. All users and grades are fictional. **Do not deploy it, expose it via ngrok/tunnels, or enter real credentials.**

## Run (Windows, macOS, Linux)

Requirements: Python 3.9+ and a browser. No packages, database server, Node.js, Docker, or internet access required after download.

1. Download this repository as ZIP from GitHub and extract it, or run `git clone <repository-url>`.
2. Open a terminal **inside** the extracted `cuboai-workshop` folder.
3. Run one of these commands:

   - **Windows:** `py server.py --reset` (or `python server.py --reset`)
   - **Mac/Linux:** `python3 server.py --reset`

4. Open **http://127.0.0.1:8765** in your browser.
5. Sign in using `alex / alex123` or `sam / sam123`. An instructor demo account is `admin / admin123`.

If the browser says the page is unavailable, check whether Python is installed and whether the terminal shows an error. If port 8765 is busy, close the other workshop instance.

Stop with **Ctrl+C**. To reset grades and accounts to their original values, stop and run the command with `--reset` again. All changes to demo data will be erased.

## Challenge: It works. But can you trust it?

Explore the app, then ask your AI coding agent to understand, verify, and fix unexpected behavior.

1. Find at least one **authorization** issue, and demonstrate it using only demo accounts.
2. Look for UI functionality that says it succeeded but didn't actually persist anything.
3. Find an **input validation** edge case.
4. Write an automated test that **fails before** your fix and **passes after** it.
5. Explain what your AI agent actually executed versus what it merely claimed.

Useful agent prompt:

> Investigate this local training app. First explain its authentication, authorization, and data flows. Propose three negative tests. Do not modify anything until you can reproduce an issue with a test. Then fix one issue minimally and rerun the test. Report commands and results honestly.

## Safety

This project is deliberately insecure. It binds to `127.0.0.1` only. Don't change this binding or publish it. Don't use real names, passwords, tokens, or user data. Never copy code from this demo directly into production.
