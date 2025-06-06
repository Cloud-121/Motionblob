#Simple script just to quickly setup the virtual env and run the logging script
# It's just here to make my life easier x3

if [ -d "venv" ]; then
    . venv/bin/activate
else
    python -m venv venv
    . venv/bin/activate
    python -m pip install -r requirments.txt
fi

python capturelogs.py