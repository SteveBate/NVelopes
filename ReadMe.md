# NVelopes

## What is it?

A playground/prototype API for a hypothetical SaaS implementation of a budgeting system that your gran and grandad probably used before there were such things as computers whereby they would partition their income into envelopes and write on each envelope what the cash was for i.e which bills to pay. This allows for a nice, visually simple overview of how your money is allocated so you don't overspend and is far less complicated than the traditional accounting/budgeting systems that most people are familiar with.

The solution explores the use of Docker, MongoDB, JWTs, and is a reference project (for me) for how an application/service might be built this way in Python.

## Why?

1) It's a system I have used since 2006 in one form or another on various platforms (because I hate finances!)
2) It's simple enough to make it a worthy one-man project to implement but has enough depth to make it challenging
3) I wanted to have something to do in a language that I don't normally use and for this I chose Python

## Requirements

Docker - the database cluster runs locally using Bitnami docker images and allows local development making use of MongoDB transaction support which requires a clustered deployment.

## Getting started

Clone the project and create a shared network:

    docker network create -d bridge nvelopes-network

Before the application is executed you need a database. In the containers/mongo directory bring up the mongo cluster via **docker-compose up -d** or in VS Code use the docker extension, right-click the on the mongo docker-compose.yml file and select **Compose Up**.

One the database is up and running you can run the application locally by launching the application from the commandline. This will pick up the DB connection string from the .env file:

    uvicorn main:app --reload

Alternatively, build the docker image:

    docker image build -t stevebate/devrepo/nvelopes:v1 .

and run as a container explicitly setting the connection string environment variable:

    docker run -p 8000:8000 --network="nvelopes-network" -e DB_CONNECTION_STRING='mongodb://dbUser1:dbPassword1@mongo1:27017,mongo2:27017,mongo3:27017/nvelopes?authSource=nvelopes&replicaSet=rs0&readPreference=primary&ssl=false' stevebate/devrepo/nvelopes:v1

To co-ordinate all the moving parts and bring up the entire application including creating the network and launching the mongo database cluster, use the shell script file for convenience:

    ./system-up.sh

Likewise, to cleanly bring them all down and dispose the network:

    ./system-down.sh

## Tests

To run the domain model unit tests:

    python -m unittest tests.account_tests

## Usage

Once up and running, head to local **http://localhost:8000/docs#/** to see the generate OpenAPI documentation. From here you can exercise the API by creating an account and logging in via the Authorize button which will ensure the JWT token is automatically sent to every protected URI thereafter. Creating an account will return an account id which you can then use as part of the request to all other endpoints.


Alternatively, the enpoints can also be exercised via an included **requests.http** file which can be executed in VS Code via the REST Client extension. This requires a bit more involvement i.e. copying and pasting of values. For example, once you login you need to copy the returned JTW token to the variable **@token** declared at the top of the file. This is referenced in other protected endoints via the Authorization header. Also, creating an account requires that the returned **account_id** value is copied to those requests that require the account id to be passed.

## Points of interest

### Functionality

A personal budgeting application needs to allow mistakes to be corrected. Unlike an actual bank account where the transactions are append-only, and any errors are made good via a new compensating transaction issued by the bank, this application allows transaction to be undone so the user can correct mistakes as they make entries into their budegting envelopes. There is no limit to this **undo** functionality except for the fact that very first transaction i.e opening the account, cannot be undone.

### Schema Design

MongoDB is often described as schema-less but that's not strictly true. You still need to think about the best way to model your application's data. Therefore, the design of the MongoDB schema should always be based on the needs of the application. This particular application represents a bank account and a list of transactions much like an e-commerce site would model an order and a list of line items. However, while there are similararities between the two, there is one major difference that could affect performance in a big way and that is **lifetime**.

An order in an e-commerce application is likely short lived and will have not so many line items. In this case it reasonable to model the schema with the line items embedded in the order and save on a join at query time. It's also highly likely that you would always want to see the line items and order header at the same time which again points to having the line items embedded in the order.

On the other hand, a bank account is a very long lived entity. People rarely change banks, and the number of transactions (line items) associated with an account could number in the millions over the course of a persons life. This makes embedding the transactions inside the account a non-starter as the hit on performance would grow overtime. It would also eventually most likely hit the MongoDB document size limit of 16MB which again, when you think about it, makes the idea of embedding the transactions in the account document seem ludicrous. Finally, a user doesn't always want to see their transactions when viewing an account, and certainly not all of them, so when there is a need to view data independently, that too points to having separate collections for the data even if logically an account and it's transactions are  in DDD terms, an **Aggregate**, and with MongoDBs recent support for multi-document transactions there's nothing stopping you from updating an account and transactions atomically as an Aggregate requires.

This application has collections for users, accounts, and transactions. The transactions endpoint allows paging to reduce the number of returned records for any given request.
