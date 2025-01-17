# YWH programs selector

## Description
This script analyzes your YesWeHack private programs and reports, then prioritizes available programs to identify optimal targets for your next hunt.

The scoring algorithm assigns points to programs based on strategic criteria:
* Recently updated programs receive higher scores than older ones
* Programs with fewer reports are prioritized over heavily reported ones
* Programs offering wildcard scopes rank higher than single-URL targets
* ... and more

All configuration values can be customized to align with your hunting preferences and strategy.

Additionally, the tool enables program comparison with other hunters, facilitating the identification of promising collaborations!


## Usage

### Setup
```bash
$> pip install -r requirements.txt
```

### Options

```bash
usage: ywh_program_selector.py [-h] --token TOKEN [--silent] (--show | --collab-export-ids | --collaborations | --get-progs | --extract-scopes) [--ids-files IDS_FILES]

Retrieve all your YesWeHack private info in one place.

options:
  -h, --help                Show this help message and exit
  --token TOKEN             The YesWeHack authorization bearer
  --silent                  Do not print banner
  --show                    Display all programs info
  --collab-export-ids       Export all programs collaboration ids
  --collaborations          Show collaboration programs with other hunters
  --get-progs               Displays programs simple list with slugs
  --extract-scopes          Extract program scopes
  --ids-files IDS_FILES     Comma separated list of paths to other hunter IDs. Ex. user1.json,user2.json
```

<u>**Export your private program info into a nice table**</u>
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --show
```

![Tool results](./doc/results.png)

<u>**Export your private program collaboration ids**</u>
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --collab-export-ids > my-ids.json
```

<u>**Check your private programs in common with others hunters**</u>
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --collaborations --ids-files "my-ids.json, hunter1-ids.json, hunter2-ids.json"
```
![Collaboration feature](./doc/collaborations.png)

<u>**Display programs list with slugs**</u>
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --get-progs
```

<u>**Extract your private scopes into files**</u>
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --extract-scopes
```

<u>**Extract your private scopes into files for one program**</u>
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --extract-scopes --program <PROG_SLUG>
```

## TODO
* Use multithreading to speed up the data fetching ?
* Implement a login/password/otp authentication ?
* Extract all points values in config to allow fine tuning