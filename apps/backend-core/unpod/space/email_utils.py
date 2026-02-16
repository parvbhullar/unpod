INVITE_TYPE = {"space": "space", "organization": "organization"}


def get_invite_mail_body(
    invite_link, name, invite_by, valid_upto, invite_type, app_name
):
    message = f"<p>Dear ,</p>"
    message += f"<p>{invite_by or app_name} has requested you to join the {INVITE_TYPE[invite_type]} <strong> {name} </strong></p>"
    message += f"<p><a href='{invite_link}'>Click here </a> to join the {INVITE_TYPE[invite_type]}</p>"
    message += (
        f"<p>This invite link is valid till {valid_upto.strftime('%d-%m-%Y')}</p>"
    )
    message += f"<p>Please copy below link if above link not opening </p>"
    message += f"<p> <strong> {invite_link} </strong> </p>"
    message += "<p>If you are receiving this mail in spam and unable to click on link, please move this email from the Spam folder.</p>"
    # message += f"<br/>"
    message += "<p>Regards<br>"
    message += f"<p>{app_name} Team</p>"
    subject = f"{invite_by or app_name} <> {name} on {app_name}"
    return message, subject
