
# Tweet Scheduler 🐦

This repository contains a script to schedule and publish tweets using data from a Google Apps Script deployment. The script fetches anecdotes and threads, processes them, and publishes them on Twitter at scheduled times. Additionally, it handles images and polls for anecdotes.

## Features ✨

- Fetch data from a Google Apps Script deployment.
- Schedule and publish tweets using Tweepy.
- Handle images and polls for tweets.
- Use GitHub Actions to automate the process.

## Repository Structure 📂

- `requirements.txt`: Lists the dependencies required for the project.
- `tweet.json`: Stores the tweets data.
- `main.py`: The main script to schedule and publish tweets.
- `.github/workflows/main.yml`: The GitHub Actions workflow file.

## Setup 🛠️

1. **Clone the repository:**

    ```bash
    git clone https://github.com/gaulerie/schedule-tweet.git
    cd schedule-tweet
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables:**

    Create a `.env` file with the following content (on GitHub, create Secrets) :

    ```env
    TWITTER_CONSUMER_KEY=your_consumer_key
    TWITTER_CONSUMER_SECRET_KEY=your_consumer_secret_key
    TWITTER_ACCESS_TOKEN=your_access_token
    TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
    TWITTER_BEARER_TOKEN=your_bearer_token
    ```

4. **Update the URL for the Google Apps Script deployment:**

    In `main.py`, update the `url` variable with your deployment URL.

    ```python
    url = "https://script.google.com/macros/s/your-deployment-url/exec"
    ```

## Running the Script 🚀

You can run the script manually by executing:

```bash
python main.py
```

## GitHub Actions Workflow ⚙️

The GitHub Actions workflow is defined in `.github/workflows/main.yml`. It automates the process of checking for updates and publishing tweets.

### Workflow Steps:

1. **Checkout the repository:**

    ```yaml
    - uses: actions/checkout@v3
    ```

2. **Install dependencies:**

    ```yaml
    - name: Install dependency
      run: python -m pip install tweepy pendulum requests
    ```

3. **Run the script:**

    ```yaml
    - name: Run script
      env:
        TWITTER_CONSUMER_KEY: ${{ secrets.TWITTER_CONSUMER_KEY }}
        TWITTER_CONSUMER_SECRET_KEY: ${{ secrets.TWITTER_CONSUMER_SECRET_KEY }}
        TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
        TWITTER_ACCESS_TOKEN_SECRET: ${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }}
        TWITTER_BEARER_TOKEN: ${{ secrets.TWITTER_BEARER_TOKEN }}
      run: python main.py
    ```

4. **Verify changed files:**

    ```yaml
    - name: Verify Changed files
      uses: tj-actions/verify-changed-files@v10
      id: verify-changed-files
      with:
        files: |
          tweet.json
          **/*.jpeg
          **/*.jpg
          **/*.png
          **/*.gif
    ```

5. **Commit and push changes:**

    ```yaml
    - name: Commit and Push only when files change.
      if: steps.verify-changed-files.outputs.files_changed == 'true'
      run: |
        git config --global user.name 'Automated Publisher'
        git config --global user.email 'actions@users.noreply.github.com'
        git add -A
        git commit -am "Future tweet"
        git push
    ```

## License 📄

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing 🤝

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
