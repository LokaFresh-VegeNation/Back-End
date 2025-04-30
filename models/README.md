# Models Documentation

This folder contains pre-trained forecasting models based on the **STL-ATTLSTM** architecture. These models were saved in both **`.h5`** and **Keras format directories**, making them ready for deployment in the application.

---

## 📦 Model Formats

Each model is stored in two formats:
- **`.h5` format**: Compact and suitable for quick loading.
- **Keras SavedModel format**: A folder containing the full model architecture, weights, and training configuration for production deployment.

---

## 🧠 Model Variants

### 1️⃣ Single-Output Models
These models are trained separately for each commodity:

- `bm_model` → **Shallot (Bawang Merah)**
- `bp_model` → **Garlic (Bawang Putih)**
- `cr_model` → **Bird's Eye Chili (Cabai Rawit)**

This approach allows each model to specialize in forecasting one specific commodity.

---

### 3️⃣ Multi-Output Model
- `multioutput_model` → A single model trained to forecast **all three commodities simultaneously**.
- Outputs are in the order: `[Bawang Merah, Bawang Putih, Cabai Rawit]`.

This approach reduces complexity and makes deployment more efficient when forecasting all commodities at once.

---

## ⚙️ Deployment Notes

These models are intended to be used in an application environment. When loading the models, make sure to use the correct method depending on the format:

- For `.h5` models:
  ```python
  from tensorflow.keras.models import load_model
  model = load_model('bm_model.h5')
