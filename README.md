![Logo](https://raw.githubusercontent.com/jdouliez/ywh_program_selector/refs/heads/main/doc/banner.png)

<p align="center">  
    YWH Programs Selector is a CLI tool to filter bug bounty programs from platforms like YesWeHack.  
    It analyzes your YesWeHack private programs and reports, prioritizing them to identify optimal targets for your next hunt. It supports program comparison with other hunters and scope extraction for payload spraying.<br/><br/>
    <a href="https://twitter.com/intent/follow?screen_name=_Ali4s_" title="Follow"><img src="https://img.shields.io/twitter/follow/_Ali4s__?label=_Ali4s_&style=social"></a>
<a href="https://www.linkedin.com/in/jordan-douliez/" title="Connect on LinkedIn"><img src="https://img.shields.io/badge/LinkedIn-Connect-blue?style=social&logo=linkedin" alt="LinkedIn Badge"></a>
</p>

## Description

The scoring algorithm assigns points to programs based on strategic criteria:

* Recently updated programs receive higher scores than older ones
* Programs with fewer reports are prioritized over heavily reported ones
* Programs offering wildcard scopes rank higher than single-URL targets
* ... and more

All configuration values can be customized to align with your hunting preferences and strategy.

Additionally, the tool enables program comparison with other hunters, facilitating the identification of promising collaborations!

You can also extract all your program scopes in one place to spray payloads.

Authentication can be fully automated or provided manually by a bearer.

## Features

- [X] **Program Scoring**: Prioritizes programs based on updates, reports, and scope types.
- [X] **Collaboration**: Identifies common programs with other hunters.
- [X] **Scope Extraction**: Extracts program scopes for further analysis.
- [X] **Authentication**: Supports both automated and manual methods.
- [X] **Scope Finding**: Find a program from a specific scope URL.

## Installation

```bash
pip install ywh-program-selector
```

**Requirements**: Python >= 3.9

## Authentication

If you want to fully automate the authentication part, you will be asked to provide your username/email, your password and your TOTP secret key.

All credentials are stored locally in `$HOME/.config/ywh_program_selector/credentials`.

**How to obtain my TOTP secret key?**
This data is only displayed once when you set up your OTP authentication from the YWH website.
If you have not noted it previously, you must deactivate and reactivate your MFA options.

## Usage

```bash
usage: ywh-program-selector [-h] [--silent] [--force-refresh]
                            (--token TOKEN | --local-auth | --auth-file AUTH_FILE | --no-auth)
                            (--show | --collab-export-ids | --collaborations | --get-progs | --extract-scopes | --find-by-scope SCOPE)
                            [--ids-files IDS_FILES] [--program PROGRAM] [-o OUTPUT] [-f {json,plain}]

CLI tool to help bug hunters manage and prioritize their YesWeHack (YWH) private programs.

options:
  -h, --help                          Show this help message and exit
  --silent                            Do not print banner
  --force-refresh                     Force data refresh

Authentication:
  --token TOKEN                       Use the YesWeHack authorization bearer for auth
  --local-auth                        Use local credentials for auth
  --auth-file AUTH_FILE               Path to credentials file for auth
  --no-auth                           Do not authenticate to YWH

Actions:
  --show                              Display all programs info with scoring
  --collab-export-ids                 Export all programs collaboration IDs
  --collaborations                    Show collaboration programs with other hunters
  --get-progs                         Display programs simple list with slugs
  --extract-scopes                    Extract program scopes
  --find-by-scope SCOPE               Find a program by one of its scopes

Additional Options:
  --ids-files IDS_FILES               Comma separated list of paths to other hunter IDs
  --program PROGRAM                   Program slug (for --extract-scopes)
  -o, --output OUTPUT                 Output file/directory path
  -f, --format {json,plain}           Output format (default: plain)
```

### Basic Commands

- **Show programs with scoring**:

  ```bash
  ywh-program-selector --local-auth --show
  # or with token
  ywh-program-selector --token <YWH_TOKEN> --show
  ```

  ![Tool results](https://raw.githubusercontent.com/jdouliez/ywh_program_selector/refs/heads/main/doc/results.png)

- **Export your collaboration IDs**:

  ```bash
  ywh-program-selector --local-auth --collab-export-ids -o my-ids.json
  ```

- **Find possible collaborations from other hunters' IDs**:

  ```bash
  ywh-program-selector --local-auth --collaborations --ids-files "my-ids.json,hunter1-ids.json"
  ```

  ![Collaboration feature](https://raw.githubusercontent.com/jdouliez/ywh_program_selector/refs/heads/main/doc/collaborations.png)

- **Extract all scopes**:

  ```bash
  # JSON format
  ywh-program-selector --local-auth --extract-scopes -o scopes.json -f json

  # Plain text (multiple files in output directory)
  ywh-program-selector --local-auth --extract-scopes -o /tmp/scopes -f plain
  ```

- **Extract scopes for a specific program**:

  ```bash
  ywh-program-selector --local-auth --extract-scopes --program <PROG_SLUG>
  ```

- **Display programs list with slugs**:

  ```bash
  ywh-program-selector --local-auth --get-progs
  ```

- **Find program by scope URL**:

  ```bash
  ywh-program-selector --local-auth --find-by-scope "example.com"
  ywh-program-selector --local-auth --find-by-scope "https://api.example.com"
  ```

### Authentication Options

| Option | Description |
|--------|-------------|
| `--token <TOKEN>` | Use YesWeHack authorization bearer directly |
| `--local-auth` | Use credentials from default config path |
| `--auth-file <PATH>` | Use credentials from a custom file path |
| `--no-auth` | Use cached data without authentication |

### Other Options

| Option | Description |
|--------|-------------|
| `--silent` | Suppress banner output |
| `--force-refresh` | Force data refresh from API |
| `-o, --output` | Output file/directory path |
| `-f, --format` | Output format: `json` or `plain` |

## Configuration

- **Credentials**: Stored in `$HOME/.config/ywh_program_selector/credentials`. This file is managed by the tool and has restricted permissions (0600).
- **Cache**: Program data is cached in the system temp directory and auto-refreshes after 2 days.
- **Output Formats**: JSON and plain text supported.

### Scoring Configuration

You can customize the scoring thresholds by modifying `ywh_program_selector/config.py`:

```python
# Scope thresholds
SCOPE_COUNT_THRESHOLD_1 = 3      # Programs with <= 3 scopes get low score
SCOPE_COUNT_THRESHOLD_2 = 8      # Programs with <= 8 scopes get medium score

# Report thresholds  
REPORT_COUNT_PER_SCOPE_THRESHOLD_1 = 5   # Low competition
REPORT_COUNT_PER_SCOPE_THRESHOLD_2 = 15  # Medium competition

# And more...
```

## Development

```bash
# Clone the repository
git clone https://github.com/jdouliez/ywh_program_selector.git
cd ywh_program_selector

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black ywh_program_selector/
isort ywh_program_selector/
```

## License

The MIT License is a permissive free software license originating at the Massachusetts Institute of Technology (MIT). It is a simple and easy-to-understand license that places very few restrictions on reuse, making it a popular choice for open source projects. Under the MIT License, users are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the original copyright notice and permission notice are included in all copies or substantial portions of the software. The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

The YWH Programs Selector tool is licensed under the MIT License, which means it can be freely used and modified by anyone. This tool helps users analyze and prioritize their YesWeHack private programs and reports, facilitating program comparison and scope extraction. By using the MIT License, the tool encourages collaboration and sharing within the community, allowing users to adapt the tool to their specific needs while contributing to its ongoing development and improvement.

## Contributing

Pull requests are welcome. Feel free to open an issue if you want to add other features.
Beers as well...
