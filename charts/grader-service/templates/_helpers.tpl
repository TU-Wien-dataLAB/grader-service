{{/*
Expand the name of the chart.
*/}}
{{- define "grader-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "grader-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "grader-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "grader-service.labels" -}}
helm.sh/chart: {{ include "grader-service.chart" . }}
{{ include "grader-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "grader-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "grader-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "grader-service.serviceAccountName" -}}
{{- include "grader-service.fullname" . }}
{{- end }}

{{/*
Resolve a value-or-secret field.
Accepts a value that is either a plain string or a map with a `secretKeyRef` key.
Usage: {{ include "grader-service.envVar" (dict "name" "GRADER_DB_URL" "val" .Values.db.url) }}
*/}}
{{- define "grader-service.envVar" -}}
- name: {{ .name }}
{{- if eq (kindOf .val) "map" }}
  valueFrom:
    secretKeyRef:
      name: {{ .val.secretKeyRef.name }}
      key: {{ .val.secretKeyRef.key }}
{{- else }}
  value: {{ .val | quote }}
{{- end }}
{{- end }}

{{/*
Database environment variable.
Injects GRADER_DB_URL from a plain value or a secretKeyRef.
This is used by all containers that need database access (main, worker, db-migration).
*/}}
{{- define "grader-service.dbEnv" -}}
{{ include "grader-service.envVar" (dict "name" "GRADER_DB_URL" "val" .Values.db.url) }}
{{- end }}

{{/*
LTI private key environment variable.
Only rendered when LTI is enabled.
If the value is a secretKeyRef map it is injected as an env var;
otherwise it is written into the config file directly and no env var is needed.
*/}}
{{- define "grader-service.ltiEnv" -}}
{{- if and .Values.ltiSyncGrades.enabled (eq (kindOf .Values.ltiSyncGrades.token_private_key) "map") }}
{{ include "grader-service.envVar" (dict "name" "LTI_PRIVATE_KEY" "val" .Values.ltiSyncGrades.token_private_key) }}
{{- end }}
{{- end }}

{{/*
RabbitMQ credential environment variables.
*/}}
{{- define "grader-service.rabbitmqEnv" -}}
- name: RABBITMQ_GRADER_SERVICE_USERNAME
  valueFrom:
    secretKeyRef:
      key: username
      name: rabbitmq-grader-service-default-user
- name: RABBITMQ_GRADER_SERVICE_PASSWORD
  valueFrom:
    secretKeyRef:
      key: password
      name: rabbitmq-grader-service-default-user
{{- end }}

{{/*
Extra environment variables (supports value, valueFrom, and legacy secretKeyRef).
*/}}
{{- define "grader-service.extraEnv" -}}
{{- range . }}
- name: {{ .name }}
{{- if .value }}
  value: {{ .value | quote }}
{{- else if .valueFrom }}
  valueFrom:
    {{- toYaml .valueFrom | nindent 4 }}
{{- else if .secretKeyRef }}
  valueFrom:
    secretKeyRef:
      name: {{ .secretKeyRef.name }}
      key: {{ .secretKeyRef.key }}
{{- end }}
{{- end }}
{{- end }}

{{/*
envFrom block for mounting entire Secrets/ConfigMaps as env vars.
Usage: {{ include "grader-service.envFrom" (list .Values.extraEnvFrom .Values.workers.extraEnvFrom) }}
*/}}
{{- define "grader-service.envFrom" -}}
{{- $sources := list }}
{{- range . }}
  {{- if . }}
    {{- $sources = concat $sources . }}
  {{- end }}
{{- end }}
{{- if $sources }}
envFrom:
  {{- toYaml $sources | nindent 2 }}
{{- end }}
{{- end }}
