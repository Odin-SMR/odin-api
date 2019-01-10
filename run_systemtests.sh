find . -type d -name __pycache__ \
     -o \( -type f -name '*.py[co]' \) -print0 \
    | xargs -0 rm -rf
tox "$@"
