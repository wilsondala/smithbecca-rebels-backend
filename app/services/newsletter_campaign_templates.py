def campaign_email(subject: str, title: str, message: str, cta_text: str | None, cta_url: str | None):
    safe_cta_text = cta_text or "Ver novidades"

    # plaintext
    text = f"{title}\n\n{message}\n"
    if cta_url:
        text += f"\n{safe_cta_text}: {cta_url}\n"
    text += "\n— Paixão Angola"

    # html (mesmo visual “luxo”)
    button_html = ""
    if cta_url:
        button_html = f"""
        <div style="margin-top:14px;">
          <a href="{cta_url}" style="
            display:inline-block;
            padding:12px 16px;
            border-radius:999px;
            background: linear-gradient(90deg,#9b1c2c,#7d1220);
            color:#ffffff;
            text-decoration:none;
            font-weight:800;
            letter-spacing:.02em;
          ">{safe_cta_text}</a>
        </div>
        """

    html = f"""
    <div style="font-family:Arial,sans-serif;background:#0a0606;padding:24px;">
      <div style="max-width:640px;margin:0 auto;background:rgba(15,10,10,0.96);border:1px solid rgba(232,185,35,0.25);border-radius:16px;padding:22px;">
        <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#e8b923;font-weight:800;">
          Paixão Angola • Newsletter
        </div>

        <h2 style="color:#f5ede0;margin:10px 0 6px 0;">{title}</h2>

        <p style="color:rgba(245,237,224,0.88);margin:0;line-height:1.6;white-space:pre-line;">
          {message}
        </p>

        {button_html}

        <p style="color:rgba(245,237,224,0.55);margin:18px 0 0 0;font-size:12px;">
          Você está recebendo este e-mail porque se cadastrou para receber novidades da Paixão Angola.
        </p>
      </div>
    </div>
    """

    return subject, html, text