conda create -n thesis python=3.7 anaconda pywin32 pip jupyterlab qgrid ipywidgets jupyterlab_code_formatter jupyterlab-git nodejs pycairo pathos matplotlib
conda activate thesis 
pip install https://download.lfd.uci.edu/pythonlibs/q5gtlas7/python_igraph-0.7.1.post6-cp37-cp37m-win_amd64.whl

jupyter nbextension enable --py --sys-prefix widgetsnbextension
jupyter nbextension enable --py --sys-prefix qgrid

jupyter labextension install @jupyter-widgets/jupyterlab-manager @ryantam626/jupyterlab_code_formatter @jupyterlab/git qgrid

jupyter serverextension enable --py jupyterlab_code_formatter
jupyter serverextension enable --py jupyterlab_git
