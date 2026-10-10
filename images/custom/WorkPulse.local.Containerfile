FROM workpulse:16

USER root

COPY --chown=frappe:frappe apps/workpulse /home/frappe/frappe-bench/apps/workpulse

USER frappe

RUN cd /home/frappe/frappe-bench && bench pip install --quiet -e apps/workpulse

# Compile WorkPulse desk assets into the image so the mounted sites volume does
# not need Node/Yarn or a build step at runtime.
RUN cd /home/frappe/frappe-bench \
    && rm -f config/bench_build.lock \
    && bench build --app workpulse \
    && ln -sfn /home/frappe/frappe-bench/apps/workpulse/workpulse/public assets/workpulse