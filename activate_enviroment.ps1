$local_python_dir = "local_python_env" # if this is changed, .gitignore MUST be changed also!!!
$venv_path = "venv"
$local_python_version = "3.10.5" # must be 3.x.x format

Invoke-Expression ".\$local_python_dir\$venv_path\Scripts\activate"