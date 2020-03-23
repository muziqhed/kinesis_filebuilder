# Kinesis filebuilder

This utility can be built into an AWS Lambda function used to reconstruct series of file chunks consumed via Amazon Kinesis stream, where the stream consists of partitioned file data of the form
```
{
    "putEndpoint": "https://www.example.com/textfile.txt",
    "partition": 0,
    "partitionCount": 2,
    "content": "aGVsbG8gd29ybGQh"
}
```
where "content" is base64 encoded. putEndpoint will be used as a unique descriptor for each file; using this endpoint, filebuilder will reassemble each file and send it to putEndpoint via PUT request.

## Preparing your environment

The following instructions assume a Linux operating environment. As a prerequisite, you must have the AWS CLI installed locally and configured with the appropriate credentials for your account. See ["Installing the AWS CLI"](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html). Additionally, you'll need Python3.6+. The AWS account you're using will need to have appropriate roles created and available, namely the AWSLambdaKinesisExecutionRole, in order to connect the Kinesis stream event trigger to the Lambda function you'll be creating. For more details on creating this role in your AWS account, see ["AWS Lambda Execution Role"](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html).  Also required is an existing Kinesis data stream providing the above descibed content. If you have not been provided access to such a stream already and wish to create one, take a look at ["Creating and Updating Data Streams."](https://docs.aws.amazon.com/streams/latest/dev/amazon-kinesis-streams.html) For the purposes of this documentation, we'll assume an existing stream of the name "streaming-file-builder-input."


## Creating the Lambda function
 Once you have the CLI configured and the role created, you're ready to create your function, zip and upload the archive, and begin processing data. We'll begin by creating a Lambda function via the AWS console. Select the Lambda service from the console search bar,


![Select lambda](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/select_lambda.png?raw=true)


then, select "create function" from the following screen,


![create function](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/create_function.png?raw=true)


From here, we'll fill out the create function form. This is where you'll use the role you created above, and define the name for your function. The runtime we'll be using is Python3.6. Once this is done, select "create function."


![create function form](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/create_function_form.png?raw=true)


On the following screen, we'll begin to connect our Kinesis stream. Select "add trigger."


![add trigger](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/add_trigger.png?raw=true)



Our trigger will be the aformentioned Kinesis stream; we'll first select the Kinesis service as the source:



![trigger config 1](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/trigger_config_1.png?raw=true)


Then, we'll select the source stream and click "add."


![configure trigger 2](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/configure_trigger_2.png?raw=true)


We'll now find ourselves on the dashboard for our Lambda function. We're almost ready to zip and upload our code! First, though, we must configure the handler name. In the "Handler" field, enter "filebuilder.lambda_handler" and click "save."


![name handler](https://github.com/muziqhed/kinesis_filebuilder/blob/master/images/name_handler.png?raw=true)


 We've successfully created our Lambda function and connected our Kinesis trigger. We'll now update the function with the filebuilder code using the AWS CLI. Our function has Python dependencies, so we'll be creating a virtual environment to send along with it to Lambda. Once the repo has been cloned, enter the kinesis_filebuilder directory and create a virtual environment using venv by executing

 ```
 python3 -m venv my-env
 ```
 Next, activate the virtual environment:
 ```
 source my-env/bin/activate
 ```
 We'll now download our dependencies, using the command
 ```
 pip install -r requirements.txt
 ```
 Changing directories into the virtual environment's site-packages folder,
 ```
 cd my-env/lib/python3.6/site-packages/
 ```
we'll first zip up all of our dependencies in an archive having the same name as our Lambda function:
```
zip -r9 ${OLDPWD}/your_function_name.zip .
```
Returning to the root directory of the repo, we now add our the filebuilder module and its .conf file, in which is defined the temp directory for writing the assembled files:
```
cd ${OLDPWD} && zip -g your_function_name.zip filebuilder.py filebuilder_conf.json
```

 Using the AWS CLI, update your function's code with the filebuilder zip package (for more details on the arguments available, take a look at the docs [here](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html):
 ```
 aws lambda update-function-code --function-name your_function_name --zip-file fileb://your_function_name.zip
 ```
 That's it! Your function will now process any records provided via the attached Kinesis stream.
 ## Running tests
 To invoke the unit tests defined in test_filebuilder.py, navigate to the top-level repo directory and activate the virtual environment created above,
 ```
  source my-env/bin/activate
  ```
  Once you've done this, simply invoke pytest,
  ```
  python3 -m pytest
  ```
