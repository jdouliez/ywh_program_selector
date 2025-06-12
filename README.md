
![Logo](https://raw.githubusercontent.com/jdouliez/ywh_program_selector/refs/heads/main/doc/banner.png))

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
- [x] **Program Scoring**: Prioritizes programs based on updates, reports, and scope types.
- [x] **Collaboration**: Identifies common programs with other hunters.
- [x] **Scope Extraction**: Extracts program scopes for further analysis.
- [x] **Authentication**: Supports both automated and manual methods.
- [ ] **Scope finding**: Find a program from a specific scope url

## Installation
```bash
$> pip install ywh-program-selector
```

## Authentication  
If you want to fully automate the authentication part, you will be asked to provide your username/email, your password and your TOTP secret key.

All credential are stored locally in `$HOME/.config/ywh-program-selector/credentials`.

**How to obtain my TOTP secret key?**  
This data is only displayed once when you set up your OTP authentication from the YWH website.
If you have not noted it previously, you must deactivate and reactivate your MFA options.


## Usage

```bash
usage: ywh-program-selector [-h] [--silent] [--force-refresh] (--token TOKEN | --local-auth | --no-auth)
                            (--show | --collab-export-ids | --collaborations | --get-progs | --extract-scopes | --find-by-scope FIND_BY_SCOPE)
                            [--ids-files IDS_FILES] [--program PROGRAM] [-o OUTPUT] [-f {json,plain}]

The ywh-program-selector project is a tool designed to help users manage and prioritize their YesWeHack (YWH) private programs

options:
  -h, --help                               Show this help message and exit
  --silent                                 Do not print banner
  --force-refresh                          Force data refresh
  --token TOKEN                            Use the YesWeHack authorization bearer for auth
  --local-auth                             Use local credentials for auth
  --no-auth                                Do not authenticate to YWH
  --show                                   Display all programs info
  --collab-export-ids                      Export all programs collaboration ids
  --collaborations                         Show collaboration programs with other hunters
  --get-progs                              Displays programs simple list with slugs
  --extract-scopes                         Extract program scopes
  --find-by-scope FIND_BY_SCOPE            Find a program by one of its scope
  --ids-files IDS_FILES                    Comma separated list of paths to other hunter IDs. Ex. user1.json,user2.json
  --program PROGRAM                        Program slug
  -o OUTPUT, --output OUTPUT               Output file path
  -f {json,plain}, --format {json,plain}   Output format (json, plain)

```
### Basic Commands

- **Show programs**: 
  ```bash
  $> ywh-program-selector [--token <YWH_TOKEN>] [--local-auth] --show 
  ```
  ![Tool results](https://raw.githubusercontent.com/jdouliez/ywh_program_selector/refs/heads/main/doc/results.png)

- **Export your collaboration IDs**: 
  ```bash
  $> ywh-program-selector [--token <YWH_TOKEN>] [--local-auth] --collab-export-ids -o my-ids.json
  ```
- **Find possible collaborations from others hunters ids**: 
  ```bash
  $> ywh-program-selector [--token <YWH_TOKEN>] [--local-auth] --find-collaborations --ids-files "my-ids.json, hunter1-ids.json"
  ```
  ![Collaboration feature](https://raw.githubusercontent.com/jdouliez/ywh_program_selector/refs/heads/main/doc/collaborations.png)

- **Extract all scopes**: 
  ```bash
  $> ywh-program-selector [--token <YWH_TOKEN>] [--local-auth] --extract-scopes --local-auth -o /tmp/test.json
  ```

- **Extract your private scopes for one program**
  ```bash
  $> ywh-program-selector [--token <YWH_TOKEN>] [--local-auth] --extract-scopes --program <PROG_SLUG>
  ```

- **Display programs list with slugs**
  ```bash
  $> ywh-program-selector [--token <YWH_TOKEN>] [--local-auth] --get-progs
  ```

### Options
- `--silent`: Suppress banner output.
- `--force-refresh`: Force data refresh. 
- `--token <TOKEN>`: Use YesWeHack authorization bearer for authentication.
- `--local-auth`: Use local credentials for authentication.
- `--no-auth`: Do not authenticate to YWH.

## Configuration
- **Credentials**: Stored in `$HOME/.config/ywh-program-selector/credentials`. This file is managed by the tool.
- **Output Formats**: JSON and plain text supported.

## License
The MIT License is a permissive free software license originating at the Massachusetts Institute of Technology (MIT). It is a simple and easy-to-understand license that places very few restrictions on reuse, making it a popular choice for open source projects. Under the MIT License, users are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the original copyright notice and permission notice are included in all copies or substantial portions of the software. The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

The YWH Programs Selector tool is licensed under the MIT License, which means it can be freely used and modified by anyone. This tool helps users analyze and prioritize their YesWeHack private programs and reports, facilitating program comparison and scope extraction. By using the MIT License, the tool encourages collaboration and sharing within the community, allowing users to adapt the tool to their specific needs while contributing to its ongoing development and improvement.

## Contributing
Pull requests are welcome. Feel free to open an issue if you want to add other features.  
Beers as well...
