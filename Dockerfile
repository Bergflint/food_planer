# Use the official Python image as the base image
FROM python:3.11.4

# Set the working directory in the container
WORKDIR /code

# Install dependencies
COPY Pipfile Pipfile.lock /code/
RUN pip install pipenv && pipenv install --deploy --system --dev

# Copy the Django project code into the container
COPY . /code/

#Workaround for setuptools bug 2024-07-29
RUN echo "setuptools<72" > constraints.txt

ENV PIP_CONSTRAINT=constraints.txt

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["daphne", "-p", "8000", "food_planner.asgi:application"]