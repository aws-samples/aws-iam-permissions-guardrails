
{% for scp in scps %}
## {{scp.Identifier}} 
## {{scp.Guardrail}}

### Rationale
{% for rationale in scp["Rationale"] %}
* {{rationale}}
{%- endfor %}

### References
{% for reference in scp["References"] %}
* [{{reference}}]({{reference}})
{%- endfor %}

### Test Scenarios

||Test Scenario|Steps|Expected Result|
|:-------------|:-----|:---------------|
{%- for scenario in scp["Test Scenarios"] %}
|{{loop.index}}| {{scenario["Test-Scenario"]}} | {% set stepcounter=1 %} {% for step in scenario["Steps"] %}  {{loop.index}}. {{step}} <br/> {% set stepcounter=stepcounter+1 %} {% endfor %} | {{scenario["Expected-Result"]}} |
{% endfor %}

### Example SCP Statement

```
{
  "Effect": "Deny",
  "Action": [
    {% for action in scp["IAM Actions"] -%}
    {% filter indent(width=4) %}    "{{action}}"{% if not loop.last %},{% endif %} {% endfilter %}
    {% endfor -%}
  ],
  "Resource": [
    {% for resource in scp["Resource"] -%}
    {% filter indent(width=4) %}    "{{resource}}"{% if not loop.last %},{% endif %} {% endfilter %}
    {% endfor -%}
  ],
  "Condition": {
    {% for conditions in scp["Condition"] -%}
        {% for key,value in conditions.items() -%}
          {% filter indent(width=4) %}{{key|tojson_pretty}}{% endfilter %}:{% filter indent(width=8) %}{{value|tojson_pretty}}{% endfilter -%}
        {% endfor %}
    {% endfor -%}
  }
}
```

{% endfor %}
