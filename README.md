# YWH programs selector

## Description
This script retrieves your YesWeHack private programs and reports then it sorts your available programs to highlight your next favorite targets.

Feel free to customize all the config values to make the results meet your needs.

You can also compare your programs with other hunters to find good collaborations!

## Usage

### Setup
```bash
$> pip install -r requirements.txt
```

### Run

**Export your private program info into a nice table**  
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN>
```

![Tool results](./doc/results.png)

**Export your private program collaboration ids**  
```bash
$> python ywh_program_selector.py --token <YWH_TOKEN> --collab-export-ids | tee user-ids.json
```

## TODO
* Use multithreading to speed up the data fetching ?
* Implement a login/password/otp authentication ?
<!-- * Extract all points values in config to allow fine tuning -->