def newsletter_welcome_email(name: str | None, email: str):
    display_name = name.strip() if name else "Cliente"

    subject = "✅ Bem-vindo(a) à Newsletter da Paixão Angola"

    text = (
        f"Olá, {display_name}!\n\n"
        "Seu cadastro foi confirmado com sucesso.\n"
        "Em breve você receberá nossos lançamentos e promoções.\n\n"
        "— Paixão Angola"
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;background:#0a0606;padding:24px;">
      <div style="max-width:560px;margin:0 auto;background:rgba(15,10,10,0.96);border:1px solid rgba(232,185,35,0.25);border-radius:16px;padding:22px;">
        <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#e8b923;font-weight:800;">
          Paixão Angola • Newsletter
        </div>

        <h2 style="color:#f5ede0;margin:10px 0 6px 0;">
          Olá, {display_name}!
        </h2>

        <p style="color:rgba(245,237,224,0.85);margin:0 0 14px 0;line-height:1.5;">
          Seu cadastro foi confirmado com sucesso. 🎉<br/>
          Em breve você receberá nossos <b>lançamentos</b> e <b>promoções</b>.
        </p>

        <div style="margin-top:16px;padding:12px 14px;border-radius:14px;background:rgba(232,185,35,0.08);border:1px solid rgba(232,185,35,0.22);color:#f5ede0;">
          Este e-mail foi enviado para: <b>{email}</b>
        </div>

        <p style="color:rgba(245,237,224,0.6);margin:16px 0 0 0;font-size:12px;">
          Se você não solicitou esse cadastro, pode ignorar esta mensagem.
        </p>
      </div>
    </div>
    """

    return subject, html, text