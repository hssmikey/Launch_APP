# FROM python:3 AS compile-image
# RUN apt-get update \
#   && apt-get install -y --no-install-recommends \
#   build-essential \
#   gcc
# RUN python -m venv /app/env
# ENV PATH="/app/env/bin:"
# COPY requirements.txt .
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

FROM docker:git AS build-image
# COPY --from=compile-image /app/env /app/env
# ENV PATH="/app/env/bin:$PATH"

COPY . /app
WORKDIR /app
RUN apk add --no-cache gcc g++ python3 python3-dev libc-dev linux-headers musl-dev
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 5001
CMD ["python3", "./app.py"]
# COPY --from=compiler-dependency /usr/bin/ .

# /Library/Frameworks/Python.framework/Versions/3.6/bin:/Library/Frameworks/Python.framework/Versions/3.7/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/Frameworks/Python.framework/Versions/3.6/bin:/Library/Frameworks/Python.framework/Versions/3.7/bin