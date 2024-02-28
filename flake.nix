{
  description = "A flake for the latest Python version on multiple platforms";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }: 
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        packages.python = pkgs.python3;
        defaultPackage = self.packages.${system}.python;

        devShells.default = pkgs.mkShell {
          buildInputs = [ self.packages.${system}.python ];
          shellHook = ''
            # Create virtual environment if it doesn't exist
            if [ ! -d ".venv" ]; then
              python -m venv .venv
            fi

            # Activate virtual environment
            source .venv/bin/activate

            # Install requirements. This is idempotent, so we don't need to worry
            # about running it multiple times
            python -m pip install -r requirements.txt
          '';
        };
      }
    );
}
