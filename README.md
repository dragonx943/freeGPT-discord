# freeGPT-discord

Bot Discord với trình tạo ảnh A.I. bởi ChatGPT

## Ủng hộ dự án:
- ⭐ **Star dự án:** Star dự án của [Ruu3f](https://github.com/Ruu3f/freeGPT-discord) và cả repo của [freeGPT](https://github.com/Ruu3f/freeGPT). Nó sẽ có ý nghĩa rất nhiều đối với Ruu3f! 💕
- 🎉 **Tham gia máy chủ Discord của Ruu3f:** Nhắn tin với Ruu3f và người khác [tại đây](https://dsc.gg/devhub-rsgh):

[![DiscordWidget](https://discordapp.com/api/guilds/1137347499414278204/widget.png?style=banner2)](https://dsc.gg/devhub-rsgh)

## Để bắt đầu:

1. **Tải code:** Hãy bắt đầu từ việc bạn tải code của dự án này.

2. **Cài đặt modules:** Mở cmd / Terminal của bạn ra và chạy:
```pip install -r requirements.txt```

3. **Cài đặt ứng dụng:**
    - Tạo 1 ứng dụng mới trên trang [Discord Developer Portal](https://discord.com/developers).
    - Tại phần cài đặt của ứng dụng, hãy bật `message content intent` và sao chép mã token Bot Discord của bạn.

4. **Lấy token của HuggingFace:** Truy cập [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) và tạo 1 token với quyền / vai trò `Read` role và sao chép token đó.

5. **Thêm token Bot Discord và HuggingFace token của bạn vào file config.json:**
  ```python
  {
    "HF_TOKEN": "",
    "BOT_TOKEN": ""
  }
  ```

6. **Chạy Bot:** Mở cmd / Terminal của bạn và gõ:
```python bot.py```
