# Backend for Vegenation Website
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Flask API](https://img.shields.io/badge/API-Flask-green.svg)](https://flask.palletsprojects.com/)
The official backend API for the Vegenation website, providing price predictions for key food commodities, the latest relevant articles, and an intelligent chatbot for price inquiries. This system is built with Python and Flask.

---

## Table of Contents

* [About The Project](#about-the-project)
    * [Key Features](#key-features)
    * [Built With](#built-with)
* [How It Works](#how-it-works)
    * [Price Prediction (`/predict`)](#price-prediction-predict)
    * [Article Scraping (`/get_articles`)](#article-scraping-get_articles)
    * [Commodity Chatbot (`/chatbot`)](#commodity-chatbot-chatbot)
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
* [API Endpoints & Usage](#api-endpoints--usage)
    * [POST `/predict`](#post-predict)
    * [GET `/get_articles`](#get-get_articles)
    * [POST `/chatbot`](#post-chatbot)
* [Future Enhancements](#future-enhancements)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgements](#acknowledgements)
* [Contact](#contact)

---

## About The Project

This project serves as the backend engine for the Vegenation website, offering crucial data and insights into "bahan pangan" (food commodities) in Indonesia. It aims to provide users with up-to-date price predictions, relevant news, and an interactive way to query commodity information.

### Key Features

* 📈 **Commodity Price Prediction:** Utilizes an STL ATT LSTM model to forecast prices for chili (cabai), shallots (bawang merah), and garlic (bawang putih).
* 📰 **Latest Articles:** Scrapes and delivers the newest articles related to food commodities from `detik.com`.
* 🤖 **Intelligent Chatbot:** A RAG-based system powered by Gemini LLM, allowing users to ask questions about commodity price predictions.

### Built With

* [Python](https://www.python.org/)
* [Flask](https://flask.palletsprojects.com/) - Micro web framework
* [TensorFlow](https://www.tensorflow.org/) / [Keras](https://keras.io/) - For the STL ATT LSTM model
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - For web scraping
* [Google Gemini API](https://ai.google.dev/) - For the RAG chatbot
* [scikit-learn](https://scikit-learn.org/) - Preprocessing and Model Evaluation
* [Pandas](https://pandas.pydata.org/) - Data Manipulation
* [NumPy](https://numpy.org/) - Numerical operations

---

## How It Works

The backend is structured around three core functionalities accessible via API endpoints:

### Price Prediction (`/predict`)

This route employs a **Seasonal Trend Decomposition using Loess (STL) Attention Long Short-Term Memory (ATT LSTM)** model.
* **Current Implementation:** The deployed version uses a static dataset for predictions.
* **Commodities Covered:** Chili (cabai), Shallots (bawang merah), Garlic (bawang putih).
* **Future Work:** A data pipeline for ingesting and processing daily updated dynamic datasets has been developed but is not yet deployed. This pipeline would allow for more timely and potentially more accurate predictions.

### Article Scraping (`/get_articles`)

This system uses the **Beautiful Soup** library to scrape the latest news articles concerning "bahan pangan" directly from `detik.com`. It parses the HTML content to extract relevant information, providing users with recent updates.

### Commodity Chatbot (`/chatbot`)

The chatbot leverages a **Retrieval Augmented Generation (RAG)** architecture.
1.  User queries about commodity prices are received.
2.  The system retrieves relevant context, primarily from the output of the `/predict` price prediction system.
3.  This context, along with the user's query, is then fed to the **Google Gemini Large Language Model (LLM)**.
4.  The LLM generates a natural language response based on the provided information, answering the user's questions about predicted prices for chili, shallots, and garlic.

---

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Python 3.12
* `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/LokaFresh-VegeNation/Back-End
    cd Back-End
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    Ensure you have a `requirements.txt` file in your project root.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask application:**
    ```bash
    flask run
    ```
    The API should now be running on `http://127.0.0.1:5000/` (or your configured port).

---

## API Endpoints & Usage

The following are the main API endpoints available:

### POST `/predict`

Predicts the price for specified commodities.

* **Method:** `POST`
* **Query Parameters:**
* `/vegenation/predict?comodity=cabai&num_days=7`
  * `comodity` (string): commodity that will be predicted
  * `num_days` (int): num of days to be predicted
* **Success Response (200 OK):**
    * **Content:**
        ```json
        {
          "comodity": "cabai",
          "predictions": {
              "2025-05-27": 36224.859375,
              "2025-05-28": 35706.88671875,
              "2025-05-29": 35203.2578125,
              "2025-05-30": 34742.67578125,
              "2025-05-31": 34342.51953125,
              "2025-06-01": 34015.5,
              "2025-06-02": 33760.06640625
          }
        }
    }
            ```
    * **Error Response Invalid Commodity (e.g., 400 Bad Request):**
        ```json
        {
            "error": "Invalid commodity. Choose from: cabai, bawang_merah, bawang_putih"
        }
    ```
    ```
    * **Error Response Num of days <= 0 (e.g., 400 Bad Request):**
        ```json
        {
            "error": "Invalid number of days. Must be a positive integer."
        }
    ```

### GET `/get_articles`

Retrieves the latest articles about "bahan pangan" from `detik.com`.

* **Method:** `GET`
* **Success Response (200 OK):**
    * **Content:**
        ```json
        {
        "results": [
            {
                "title": "Wamendag Dyah Roro Esti menanggapi temuan beras premium berisi medium. Ia menegaskan pentingnya pemantauan dan kerja sama dengan Satgas Pangan untuk penindakan.",
                "link": "https://akcdn.detik.net.id/community/media/visual/2025/03/03/wamendag-ri-dyah-roro-1740999615984_43.jpeg?w=250&q=90",
                "description": "Kata Wamendag Soal Temuan Beras Premium Diisi Medium",
                "date": "https://www.detik.com/sumut/berita/d-7851733/kata-wamendag-soal-temuan-beras-premium-diisi-medium",
                "Tanggal": "Rabu, 02 Apr 2025 11:30 WIB"
            }, 
            { ... }
        }
        ```

### POST `/chatbot`

Allows users to ask questions about commodity price predictions.

* **Method:** `POST`
* **Request Body (JSON):**
    ```json
    {
        "message": "Berapa perkiraan harga cabai minggu depan?"
    }
    ```
* **Success Response (200 OK):**
    * **Content:**
        ```json
        {
            "response": "Berdasarkan model prediksi kami, perkiraan harga cabai untuk minggu depan adalah Rp55.000",
        }
        ```

---

## Future Enhancements

* **Deploy Dynamic Dataset Pipeline:** Implement the existing pipeline for daily updates to the prediction model's dataset.
* **Expand Commodity Coverage:** Add more types of "bahan pangan" to the prediction system.
* **Increase Scraper Sources:** Scrape articles from more news outlets for broader coverage.
* **Advanced Chatbot Capabilities:** Enhance the chatbot with more complex query understanding and historical data recall.

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## License

Distributed under the **MIT License**. See `LICENSE.txt` for more information.

---

## Acknowledgements

* `Lokatani`
* `detik.com` for providing news articles.
* The developers of the libraries and frameworks used.

---

## Contact

Lokafresh - Vegenation 

Project Link: [LokaFresh-Vegenation](https://github.com/LokaFresh-VegeNation)

[contributors-shield]: https://img.shields.io/github/contributors/LokaFresh-VegeNation/Back-End.svg?style=for-the-badge
[contributors-url]: https://github.com/LokaFresh-VegeNation/Back-End/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/LokaFresh-VegeNation/Back-End.svg?style=for-the-badge
[forks-url]: https://github.com/LokaFresh-VegeNation/Back-End/network/members
[stars-shield]: https://img.shields.io/github/stars/LokaFresh-VegeNation/Back-End.svg?style=for-the-badge
[stars-url]: https://github.com/LokaFresh-VegeNation/Back-End/stargazers
[issues-shield]: https://img.shields.io/github/issues/LokaFresh-VegeNation/Back-End.svg?style=for-the-badge
[issues-url]: https://github.com/LokaFresh-VegeNation/Back-End/issues
[license-shield]: https://img.shields.io/github/license/LokaFresh-VegeNation/Back-End.svg?style=for-the-badge
[license-url]: https://github.com/LokaFresh-VegeNation/Back-End/blob/main/LICENSE
