# Albanian Transcriber using Machine learning | DibraSpeaks.

<p align="center">
  <img src="https://github.com/florijanqosja/Albanian-ASR/assets/55300217/8d2dec67-b6d0-47c4-8107-7ff4cd834411" alt="Logo" width="200">
</p>
This project is an AI-based transcription tool for the Albanian language. The tool is designed to automatically transcribe Albanian speech to text using Python.

## Features

- Automatic speech recognition for Albanian language with our best trained model
- User-friendly interface to label and validate speech datas
- Dataset with Albanian Speech datas.

## Installation

This project is made up of three main parts: an API that serves all the files to the UI, a section that is used to label and validate Albanian speech data, and the third part which is the model test. In the web folder are all the files needed to run the UI, in the api folder are the files needed to run the faastAPI, and in the automation folder are some scripts used for many things, including generating datasets. The folder training includes all the notebooks used to train the model.

Docker is required to run the project locally.
To run the project locally run:

```
docker-compose up --build -d
```

After all the containers are up and running you should find at:

[localhost:140](http://localhost:140/docs) -> API

[localhost:120](http://localhost:120) -> WEB



## Domains

### Production
The PRODUCTION WEB interface: [dibraspeaks.uneduashqiperine.com](http://dibraspeaks.uneduashqiperine.com/)

The PRODUCTION API: [api.uneduashqiperine.com](http://api.uneduashqiperine.com/docs)

## Dataset amd Pre-trained Models Links

https://www.kaggle.com/flooxperia/

## Contributing

We welcome all contributions to this project. If you have any ideas for new features or improvements, please feel free to create an branch, and test it by creating a pull request to merge your ticket to dev. we will try to approve the request as soon as possible and the change will be for some time in dev. After the feature or the improvement have been tested on dev than we can merge it to production.

## Writing about the project

[finalyearproject.pdf](https://github.com/florijanqosja/fypfloo/files/11585369/finalyearproject.1.pdf)

## Screenshots

Our model Architecture VS Deepspeech on our dataset

![modelscompared](https://github.com/florijanqosja/fypfloo/assets/55300217/7eec2f97-bccd-4c5a-b449-c4a8261fa099)

![valLoss](https://github.com/florijanqosja/fypfloo/assets/55300217/8d19782d-a098-4c14-9967-14cca719d0c6)

![werplot](https://github.com/florijanqosja/fypfloo/assets/55300217/d8c1ed22-10ee-48ca-8217-7ccd99362ed7)

## Authors

- [@florijanqosja](https://www.github.com/florijanqosja)

## Buy Me A Coffee

https://www.buymeacoffee.com/florijanqosja
https://github.com/sponsors/florijanqosja

## License

This project is licensed under the MIT License.
