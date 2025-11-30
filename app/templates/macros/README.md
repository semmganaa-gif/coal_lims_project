# Template Macros - Хэрэглэх заавар

Jinja2 macro-ууд ашиглан HTML template-ын код давхардлыг багасгах.

## 📁 Файлууд

- **`form_helpers.html`** - Form талбарууд, товчлуурууд
- **`table_helpers.html`** - Хүснэгт, pagination

---

## 🔧 Form Helpers

### Import хийх

```jinja
{% from 'macros/form_helpers.html' import render_field, render_submit_button %}
```

### 1. Энгийн текст талбар

```jinja
{{ render_field(form.username, placeholder='Хэрэглэгчийн нэр оруулна уу') }}
```

**Өмнөх код (давхардсан):**
```html
<div class="mb-3">
    {{ form.username.label(class="form-label fw-bold") }}
    {{ form.username(class="form-control", placeholder='Хэрэглэгчийн нэр') }}
    {% if form.username.errors %}
      <div class="invalid-feedback d-block">
        {% for error in form.username.errors %}
          <div>{{ error }}</div>
        {% endfor %}
      </div>
    {% endif %}
</div>
```

### 2. Radio button group

```jinja
{{ render_radio_group(form.client_name, inline=true, small=false) }}
```

### 3. Checkbox

```jinja
{{ render_checkbox(form.return_sample, description='Дээжийг буцааж өгнө') }}
```

### 4. Submit button

```jinja
{{ render_submit_button(form.submit, text='Хадгалах', icon='bi-check-lg') }}
```

### 5. Action buttons (Edit/Delete)

```jinja
{{ render_action_buttons(
    edit_url=url_for('admin.edit_user', user_id=user.id),
    delete_url=url_for('admin.delete_user', user_id=user.id),
    delete_confirm='Хэрэглэгчийг устгах уу?'
) }}
```

### 6. Alert message

```jinja
{{ render_alert('Амжилттай хадгалагдлаа!', category='success') }}
```

### 7. Card wrapper

```jinja
{% call render_card(title='Тохиргоо', class_='mb-3') %}
    <p>Card дотор байх контент...</p>
{% endcall %}
```

---

## 📊 Table Helpers

### Import хийх

```jinja
{% from 'macros/table_helpers.html' import data_table, render_table_header, render_empty_row %}
```

### 1. Хүснэгт үүсгэх

```jinja
{% call data_table(id='users-table', striped=true, hover=true) %}
  {{ render_table_header(['Нэр', 'И-мэйл', 'Эрх'], actions=true) }}
  <tbody>
    {% for user in users %}
      <tr>
        <td>{{ user.username }}</td>
        <td>{{ user.email }}</td>
        <td>{{ user.role }}</td>
        <td class="text-end">
          {{ render_action_buttons(
              edit_url=url_for('admin.edit_user', user_id=user.id),
              delete_url=url_for('admin.delete_user', user_id=user.id)
          ) }}
        </td>
      </tr>
    {% endfor %}
  </tbody>
{% endcall %}
```

### 2. Хоосон хүснэгт

```jinja
{{ render_empty_row(colspan=4, message='Хэрэглэгч байхгүй байна.') }}
```

### 3. Pagination

```jinja
{{ render_pagination(pagination, 'admin.users') }}
```

### 4. Status badge

```jinja
{{ render_status_badge(sample.status, label='Шинэ', variant_map={'new': 'primary'}) }}
```

---

## ✅ Давуу тал

1. **Код давхардал багассан** - Нэг macro олон газар ашиглах
2. **Тогтвортой design** - Бүх form ижил харагдах
3. **Алдаа багасах** - Нэг газар засвар хийхэд бүгд өөрчлөгдөнө
4. **Хөгжүүлэлт хурдан болох** - Шинэ template хурдан бичих

---

## 📝 Жишээ: Edit form

**Өмнө (60 мөр):**
```html
<form method="post">
    <div class="mb-3">
        <label class="form-label fw-bold">Нэр:</label>
        <input type="text" name="name" class="form-control" required>
    </div>
    <div class="mb-3">
        <label class="form-label fw-bold">И-мэйл:</label>
        <input type="email" name="email" class="form-control" required>
    </div>
    <div class="d-grid">
        <button type="submit" class="btn btn-primary">
            <i class="bi bi-check-lg"></i> Хадгалах
        </button>
    </div>
</form>
```

**Одоо (10 мөр):**
```jinja
{% from 'macros/form_helpers.html' import render_field, render_submit_button %}

<form method="post">
    {{ form.hidden_tag() }}
    {{ render_field(form.name) }}
    {{ render_field(form.email) }}
    {{ render_submit_button(form.submit, text='Хадгалах') }}
</form>
```

**80% код багассан!** 🎉

---

## 🚀 Хэрэглэх санал

1. Шинэ template үүсгэхдээ эдгээр macro-г ашиглах
2. Хуучин template-ыг аажмаар шинэчлэх
3. Өөрийн macro нэмэх (project-ын хэрэгцээнд тохируулан)

---

**Асуулт байвал:**
