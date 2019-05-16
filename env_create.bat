conda create -n oliver python=3.6 scipy pywin32 pip jupyter jupyterlab qgrid -c conda-forge ipywidgets
conda activate oliver
pip install https://download.lfd.uci.edu/pythonlibs/q5gtlas7/python_igraph-0.7.1.post6-cp36-cp36m-win_amd64.whl
pip install jupyterlab_code_formatter jupyterlab-git

jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install @ryantam626/jupyterlab_code_formatter
jupyter labextension install @jupyterlab/git

jupyter serverextension enable --py jupyterlab_code_formatter
jupyter serverextension enable --py jupyterlab_git
jupyter serverextension enable --py qgrid