# CZ Pong

TODO: CI badges

TODO: Game description

TODO: Gif of gameplay

TODO: Table of contents

## Running the Game
Running the game just requires having the correct libraries and a supported python version installed. I recommend using a venv to keep your development environments isolated, but you can also install these dependencies globally.
### Manually (Using venv)
Enter a shell in the project root folder. If you do not have pip installed as a standalone command, replace `pip` with
`python -m pip` in these instructions.

If this is the first time you are running cz-pong, create a venv and install
the dependencies (ignore this if you have already done it):
```sh
python -m venv .venv # Using the builtin python module "venv", create a virtual environment at ~/.venv.
source .venv/bin/activate # Configure this shell instance to use the new venv
pip install -r requirements.txt # Install the game's dependencies, which are listed in the file `requirements.txt`
python main.py # Run the game
```

If you have already created a venv and installed the dependencies, and just want to run the game, just run
```sh
source .venv/bin/activate # Enter the venv so that python can find the game's dependencies
python main.py # Run the game
```

### Manually (⚠️ Without venv)
Enter a shell in the project root folder. If you do not have pip installed as a standalone command, replace `pip` with
`python -m pip` in these instructions.

If this is the first time you are running cz-pong, install the needed dependencies:
```sh
pip install -r requirements.txt
```

Then, run the game:
```sh
python main.py
```

### With Nix
If you are using the Nix package manager, you can get a development environment set up by entering a shell
in the project root and running
```sh
nix develop # enter a development shell using Nix
python main.py # run the game
```

Using Nix is not necessary, but it ensures that you will not have any issues due to an incorrect python version
or conflicting library installations. This approach will also automatically manage the venv for you.

## FAQ
TODO

## Debugging
TODO

## Contributors
- Code by Seth Hinz ([sethhinz@me.com](mailto:sethhinz@me.com))
- Music by [FASSounds](https://pixabay.com/users/fassounds-3433550/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=112191) from [Pixabay](https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=112191)