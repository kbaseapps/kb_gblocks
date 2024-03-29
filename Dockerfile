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

# original source has moved.  Maintaining a copy in repo in tarballs dir in case it disappears again
# old source: http://molevol.cmima.csic.es/castresana/Gblocks/Gblocks_Linux64_0.91b.tar.Z

RUN \
    curl -o Gblocks_Linux64_0.91b.tar.Z https://www.biologiaevolutiva.org/jcastresana/Gblocks/Gblocks_Linux64_0.91b.tar.Z && \
    tar xfz Gblocks_Linux64_0.91b.tar.Z && \
    chmod 555 Gblocks_0.91b/Gblocks && \
    cp Gblocks_0.91b/Gblocks ./

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
