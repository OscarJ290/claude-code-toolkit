# Approved responses

One approved template per category that takes a reply: lead, support and billing. Each one exists in English and in Spanish. The categories `no_reply` and `needs_review` never get a draft, so they have no template.

## How to use these templates

* Pick the template of the category and the language of the email. If the email is in a language other than English or Spanish, there is no approved template: send it to `needs_review`.
* Fill only the placeholders in curly braces, and only with data that appears in the email.
* If the email does not carry the data for a placeholder, leave the placeholder visible as written, for example `{first_name}`. Never invent a value.
* Do not add, remove or reword sentences. Do not add prices, dates, deadlines, refunds, discounts or any promise. The templates promise nothing on purpose.
* Greeting and closing stay as written. The signature uses the recipient name from the `To` header of the email, which is the owner of the mailbox.

## Placeholders

| Placeholder | Where the value comes from |
| --- | --- |
| `{first_name}` | First name of the sender, from the `From` header or the signature. |
| `{topic}` | A short phrase from the email that says what it is about, in the language of the email. It must read naturally after the word "about" or "sobre". |
| `{original_subject}` | The `Subject` header of the email, without a leading `Re:`. |
| `{my_name}` | The display name in the `To` header. |

## Lead

### English

```
Subject: Re: {original_subject}

Hi {first_name},

Thank you for contacting me about {topic}. I have received your message and I am reading through the details.

If there is anything else that would help me understand what you need, feel free to reply with it here.

Best regards,
{my_name}
```

### Español

```
Asunto: Re: {original_subject}

Hola {first_name}:

Gracias por escribirme sobre {topic}. Recibí su mensaje y estoy revisando los detalles.

Si hay algo más que ayude a entender lo que necesita, puede responder a este correo con esa información.

Saludos cordiales,
{my_name}
```

## Support

### English

```
Subject: Re: {original_subject}

Hi {first_name},

Thank you for telling me about {topic}. I am sorry for the inconvenience. I have received your message and I am looking into it.

If you can share any extra detail about what happened, such as the exact message you saw or the steps you followed, please reply here.

Best regards,
{my_name}
```

### Español

```
Asunto: Re: {original_subject}

Hola {first_name}:

Gracias por avisarme sobre {topic}. Lamento las molestias. Recibí su mensaje y lo estoy revisando.

Si puede compartir algún detalle adicional de lo ocurrido, como el mensaje exacto que apareció o los pasos que siguió, responda a este correo.

Saludos cordiales,
{my_name}
```

## Billing

### English

```
Subject: Re: {original_subject}

Hi {first_name},

Thank you for your message about {topic}. I have received your request and I am checking it.

If there is any other detail about it that I should have, please reply here.

Best regards,
{my_name}
```

### Español

```
Asunto: Re: {original_subject}

Hola {first_name}:

Gracias por su mensaje sobre {topic}. Recibí su solicitud y la estoy revisando.

Si hay algún otro dato al respecto que deba tener, responda a este correo.

Saludos cordiales,
{my_name}
```
