let
  sources = import ./nix/sources.nix { };
  pkgs = import sources.nixpkgs { };
  # Python
  pythonEnv = pkgs.python38.withPackages (ps: with ps;[
    numpy
  ]);
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    pythonEnv

    imagemagick
  ];
}

