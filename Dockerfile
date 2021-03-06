FROM continuumio/anaconda3:latest

EXPOSE 8888

WORKDIR /opt/conda/bin/

RUN ./conda install jupyter -y --quiet
RUN ./conda install --quiet --yes -c ibmdecisionoptimization cplex
RUN ./conda install --quiet --yes networkx


VOLUME /opt/notebooks
VOLUME /opt/datasets
VOLUME /opt/modules
VOLUME /opt/clq

CMD ./jupyter notebook --notebook-dir=/opt/notebooks --ip='*' --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''