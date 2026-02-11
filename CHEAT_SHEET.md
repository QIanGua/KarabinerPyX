# KarabinerPyX Mapping Cheat Sheet

## Profile: KarabinerPyX Demo (Selected)

### hyper activation

| From | To | Conditions |
| :--- | :--- | :--- |
| `right_command` | → `set_variable(hyper=1)`<br>Alone: `right_command` | - |

### hyper: h -> left_arrow

| From | To | Conditions |
| :--- | :--- | :--- |
| `h` | → `left_arrow` | Var: hyper==1 |

### hyper: j -> down_arrow

| From | To | Conditions |
| :--- | :--- | :--- |
| `j` | → `down_arrow` | Var: hyper==1 |

### hyper: k -> up_arrow

| From | To | Conditions |
| :--- | :--- | :--- |
| `k` | → `up_arrow` | Var: hyper==1 |

### hyper: l -> right_arrow

| From | To | Conditions |
| :--- | :--- | :--- |
| `l` | → `right_arrow` | Var: hyper==1 |

### hyper macro: t -> typed_text

| From | To | Conditions |
| :--- | :--- | :--- |
| `t` | → `shell_command` | Var: hyper==1 |

### hyper combo j+k -> escape

| From | To | Conditions |
| :--- | :--- | :--- |
| `j + k` | → `escape` | Var: hyper==1 |

### hyper sequence: g+g

| From | To | Conditions |
| :--- | :--- | :--- |
| `g` | → `set_variable(hyper_seq_g_g_step1=1)` | Var: hyper==1 |

### hyper sequence: g+g

| From | To | Conditions |
| :--- | :--- | :--- |
| `g` | → `set_variable(hyper_seq_g_g_step2=1) + home + set_variable(hyper_seq_g_g_step1=0) + set_variable(hyper_seq_g_g_step2=0)` | Var: hyper==1<br>Var: hyper_seq_g_g_step1==1 |

### alt activation

| From | To | Conditions |
| :--- | :--- | :--- |
| `right_option` | → `set_variable(alt=1)`<br>Alone: `right_option` | - |

### alt: h -> home

| From | To | Conditions |
| :--- | :--- | :--- |
| `h` | → `home` | Var: alt==1 |

### alt: l -> end

| From | To | Conditions |
| :--- | :--- | :--- |
| `l` | → `end` | Var: alt==1 |

### alt: u -> page_up

| From | To | Conditions |
| :--- | :--- | :--- |
| `u` | → `page_up` | Var: alt==1 |

### alt: d -> page_down

| From | To | Conditions |
| :--- | :--- | :--- |
| `d` | → `page_down` | Var: alt==1 |

### hyper_alt stacked activation

| From | To | Conditions |
| :--- | :--- | :--- |
| `right_command + right_option` | → `set_variable(hyper_alt=1)` | - |

### hyper_alt: h -> left_arrow

| From | To | Conditions |
| :--- | :--- | :--- |
| `h` | → `left_arrow` | Var: hyper_alt==1 |

### hyper_alt: l -> right_arrow

| From | To | Conditions |
| :--- | :--- | :--- |
| `l` | → `right_arrow` | Var: hyper_alt==1 |

### hyper_alt macro: t -> typed_text

| From | To | Conditions |
| :--- | :--- | :--- |
| `t` | → `shell_command` | Var: hyper_alt==1 |
