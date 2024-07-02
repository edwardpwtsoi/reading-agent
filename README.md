# Reading Agent


## prerequisites

- python: 3.10^
- Azure Document Intelligence

either one of the following access:
- Azure OpenAI
- Google Gemini
- AWS Bedrock

## Setup
### Dependencies

```console
poetry install
```

### Backend

Azure Document Intelligence

```console
AZURE_FORM_RECOGNIZER_API_ENDPOINT=<api endpoint>
AZURE_FORM_RECOGNIZER_API_KEY=<your azure document intelligence api key>
```

Azure OpenAI:
```console
export GPT_API_KEY=<your api key>
export GPT_API_VERSION=<api version>
export GPT_DEPLOYMENT_NAME=<deployment name>
export GPT_ENDPOINT=<resource endpoint>
```

Google Gemini:
```console
export GEMINI_API_KEY=<your api key>
```

AWS Bedrock:
```console
AWS_ACCESS_KEY_ID=<your access key id>
AWS_SECRET_ACCESS_KEY=<your access key>
AWS_SESSION_TOKEN=<your session token>
```

#### Usage

```console
python -m reading_agent [--logging_level="DEBUG"]
```


#### Acknowledgements

```
@article{lee2024readagent,
    title={A Human-Inspired Reading Agent with Gist Memory of Very Long Contexts},
    author={Lee, Kuang-Huei and Chen, Xinyun and Furuta, Hiroki and Canny, John and Fischer, Ian},
    journal={arXiv preprint arXiv:2402.09727},
    year={2024}
}
```