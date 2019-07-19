FROM kbase/kbase:sdkbase2.latest
MAINTAINER KBase Developer [Dylan Chivian (DCChivian@lbl.gov)]

# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

# Install Gblocks
#
WORKDIR /kb/module
RUN \
    curl http://molevol.cmima.csic.es/castresana/Gblocks/Gblocks_Linux64_0.91b.tar.Z > Gblocks_Linux64_0.91b.tar.Z && \
    tar xfz Gblocks_Linux64_0.91b.tar.Z && \
    chmod 555 Gblocks_0.91b/Gblocks && \
    cp Gblocks_0.91b/Gblocks ./
    #ln -s Gblocks_0.91b/Gblocks Gblocks

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
