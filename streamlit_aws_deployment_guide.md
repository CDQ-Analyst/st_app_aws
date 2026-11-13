# Deploying a Streamlit App on AWS EC2: Step-by-Step Guide

Written 13 November 2026, from a deployment that was carried out and confirmed working.

## Overview

The finished setup has four parts:

| Part | What it does |
|---|---|
| Your computer | Where you write and test `app.py` |
| GitHub repository | Holds the code so the server can download it |
| EC2 instance | A virtual Ubuntu server on AWS that runs the app |
| systemd service | Keeps the app running in the background and restarts it after a reboot |

The flow is: write code locally, upload it to GitHub, pull it onto the EC2 server, and run it there on port 8501.

Names used in this guide (replace with your own where they differ):

- GitHub repository: `https://github.com/CDQ-Analyst/st_app_aws`
- EC2 instance name: `streamlit-app`
- Folder on the server: `/home/ubuntu/st_app_aws`
- `YOUR_PUBLIC_IP`: the instance's Public IPv4 address from the EC2 console

---

## Step 1: Prepare the app and test it locally

The project needs two files in one folder (for example `Documents\Python Scripts\st_app_aws`):

- `app.py`: the Streamlit app
- `requirements.txt`: the packages it needs, one per line

```text
streamlit
pandas
openpyxl
```

`openpyxl` is required because the app reads an uploaded Excel file. The data file (`sales_data.xlsx`) is uploaded through the app in the browser, so it does not go in the repository.

Test locally in Anaconda Prompt:

```bash
cd "C:\Users\YOUR_NAME\Documents\Python Scripts\st_app_aws"
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. Confirm it works before deploying.

---

## Step 2: Put the code on GitHub

### Create the repository

1. Sign in at github.com.
2. Click **+** (top right), then **New repository**.
3. Name it `st_app_aws` and set visibility to **Public**, so the server can download it without a login.
4. Leave "Add a README" unticked and click **Create repository**.

### Upload the files in the browser

1. On the empty repository page, click the link **uploading an existing file**, or go to `https://github.com/YOUR_USERNAME/st_app_aws/upload/main`.
2. Click **choose your files**, select `app.py` and `requirements.txt` (hold Ctrl to select both), and click **Open**.
3. Wait for both names to appear in the list, then click **Commit changes**.

### Alternative: use Git from the command line

```bash
git init
git add app.py requirements.txt
git commit -m "Simple Streamlit sales analysis app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/st_app_aws.git
git push -u origin main
```

---

## Step 3: Launch the EC2 instance

1. Sign in at console.aws.amazon.com, search for **EC2**, and open it.
2. Click **Launch instance** and fill in the form:

| Setting | Value |
|---|---|
| Name | `streamlit-app` |
| OS image | Ubuntu Server 24.04 LTS |
| Instance type | `t3.micro` or `t2.micro` (whichever is marked "Free tier eligible") |
| Key pair | Proceed without a key pair (the browser connection does not need one) |
| Storage | Default (8 GB) |

3. Under **Network settings**, click **Edit**:
   - Keep the SSH rule (port 22) with source **Anywhere**. The browser connection needs it.
   - Click **Add security group rule**: Type **Custom TCP**, Port range **8501**, Source type **Anywhere**. This opens Streamlit's port.
4. Click **Launch instance**, then **View all instances**.
5. Wait until **Instance state** shows **Running**.
6. Click the instance and copy its **Public IPv4 address**.

---

## Step 4: Connect to the server

1. On the Instances page, tick the box next to `streamlit-app`.
2. Click **Connect**.
3. On the **EC2 Instance Connect** tab, leave the username as `ubuntu` and click **Connect**.

A terminal opens in a new browser tab with a prompt like:

```text
ubuntu@ip-172-31-8-141:~$
```

---

## Step 5: Install and run the app on the server

Run each block in the server terminal.

### Install the tools

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git
```

If a pink or purple screen asks about restarting services, press Enter.

### Download the code

```bash
git clone https://github.com/CDQ-Analyst/st_app_aws.git
cd st_app_aws
ls
```

`ls` should list `app.py` and `requirements.txt`.

### Install the Python packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The prompt now starts with `(venv)`.

### Run the app (first test)

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

If it asks for an email address, press Enter to skip.

### Open it in the browser

```text
http://YOUR_PUBLIC_IP:8501
```

Use `http://`, not `https://`. Streamlit prints three addresses; only the **External URL** works from your computer:

| Address | Why it does or does not work |
|---|---|
| `localhost:8501` | Means "this same machine", so it only works from inside the server |
| `172.31.x.x:8501` | The private address, visible only inside the AWS network |
| External URL | The public address, reachable from anywhere |

Upload `sales_data.xlsx` to confirm the analysis appears.

---

## Step 6: Keep the app running permanently

Run this way, the app stops when the terminal tab closes. A systemd service fixes that.

1. Press **Ctrl+C** in the terminal to stop the app.
2. Create the service file. Paste the whole block at once. Every line must start at the left edge with no spaces in front, especially the final `EOF`.

```bash
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<'EOF'
[Unit]
Description=Streamlit app
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/st_app_aws
ExecStart=/home/ubuntu/st_app_aws/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

3. Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now streamlit
sudo systemctl status streamlit
```

Look for a green **active (running)**, then press **q**.

4. Close the terminal tab and reload the app in the browser. It should still be there.

---

## Step 7: Update the app after code changes

1. Change the code on GitHub (edit in the browser, or upload the new file).
2. Connect to the server (Step 4) and run:

```bash
cd ~/st_app_aws
git pull
sudo systemctl restart streamlit
```

3. Reload the app in the browser.

`git pull` should mention the changed file. "Already up to date" means the change was not committed on GitHub.

If `requirements.txt` gained a new package, install it before restarting:

```bash
cd ~/st_app_aws
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart streamlit
```

---

## Step 8: Stop, start, terminate, and what each costs

All three actions are under **Instance state** on the EC2 Instances page.

| Action | What happens | Cost while in that state |
|---|---|---|
| Running | App is live | Compute hours (or free-tier hours) plus disk |
| Stop instance | Server is off; code, packages and service are kept | Disk only: roughly $0.08 per GB per month, about 65 cents for 8 GB |
| Terminate instance | Server and disk are deleted for good | Nothing |

After **Start instance**:

- The app starts by itself. Nothing needs to be re-run.
- The public IP address is new each time. Copy the new **Public IPv4 address** and open `http://NEW_PUBLIC_IP:8501`.
- Allow about a minute after the state turns to Running.

The prices are approximate and vary by region. Check **Billing and Cost Management → Bills** for the real figures, and create a budget alert (for example $5) under **Billing → Budgets**.

---

## Troubleshooting

These are the problems met during this deployment and what fixed them.

| Symptom | Cause | Fix |
|---|---|---|
| `TypeError: 'stretch' has type str, but expected one of: int` | `width="stretch"` only exists in recent Streamlit versions; the local Anaconda install was older | Remove the `width` argument from `st.dataframe(...)` |
| `git clone` asks for a username and password, then "Repository not found" | The command still contained the placeholder `YOUR_USERNAME`, or the repository is private | Use the real username in the address; make the repository public |
| `Command 'lsgit' not found` | Two commands were pasted together on one line | Paste one command at a time and press Enter after each |
| Terminal shows `>` and waits after pasting the service file | The closing `EOF` had spaces in front of it | Press Ctrl+C and paste the block again with no leading spaces |
| `localhost:8501` or `172.31.x.x:8501` does not open | Those addresses only work inside the server or the AWS network | Use `http://PUBLIC_IP:8501` |
| App address stops working after a stop and start | The public IP changes on every start | Copy the new Public IPv4 address from the EC2 console |
| Page never loads at the public address | Port 8501 is not open in the security group | EC2 → instance → **Security** tab → security group → **Edit inbound rules** → add Custom TCP 8501 from Anywhere |
| App shows an error after an update | A Python error in the new code | Read the log with the commands below |

Useful commands on the server:

```bash
sudo systemctl status streamlit                  # is the app running?
sudo systemctl restart streamlit                 # restart it
sudo systemctl stop streamlit                    # stop it
sudo journalctl -u streamlit -n 30 --no-pager    # last 30 log lines, including Python errors
```

---

## Where to go next

- **Elastic IP:** a fixed public address, so the URL stops changing on every start. AWS charges a small hourly fee for it, including while the instance is stopped.
- **Restrict SSH:** change the port 22 rule from Anywhere to a narrower source once you are comfortable with how you connect.
- **Nginx and HTTPS with a domain name:** a proper `https://yourname.com` address instead of `IP:8501`.
- **Docker on ECS Fargate:** the more production-style way to deploy, without managing a server yourself.
