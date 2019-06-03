conda create -f environment.yml
conda activate thesis

jupyter nbextension enable --py --sys-prefix widgetsnbextension
jupyter nbextension enable --py --sys-prefix qgrid

jupyter labextension install @jupyter-widgets/jupyterlab-manager @ryantam626/jupyterlab_code_formatter @jupyterlab/git qgrid @jupyterlab/plotly-extension

jupyter serverextension enable --py jupyterlab_code_formatter
jupyter serverextension enable --py jupyterlab_git
