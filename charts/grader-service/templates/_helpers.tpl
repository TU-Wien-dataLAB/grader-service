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
Render a Kubernetes env var entry from the value/valueFrom pattern.
Accepts a dict with "name" (env var name) and "val" (the map from values.yaml).
The map must contain exactly one of:
  - value: <string>
  - valueFrom: { secretKeyRef: { name, key } }

Usage: {{ include "grader-service.envVar" (dict "name" "GRADER_DB_URL" "val" .Values.db.url) }}
*/}}
{{- define "grader-service.envVar" -}}
- name: {{ .name }}
{{- if hasKey .val "valueFrom" }}
  valueFrom:
    {{- toYaml .val.valueFrom | nindent 4 }}
{{- else if hasKey .val "value" }}
  value: {{ .val.value | quote }}
{{- else }}
  {{- fail (printf "%s: must contain either 'value' or 'valueFrom'. Got: %s" .name (toJson .val)) }}
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
Extra environment variables. Standard Kubernetes env var syntax only.
*/}}
{{- define "grader-service.extraEnv" -}}
{{- range . }}
- name: {{ .name }}
{{- if .value }}
  value: {{ .value | quote }}
{{- else if .valueFrom }}
  valueFrom:
    {{- toYaml .valueFrom | nindent 4 }}
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

{{/*
Extra-files volume mounts.
Generates one volumeMount per entry in .Values.extraFiles, each mounting a
single file at the configured mountPath.
Usage: {{ include "grader-service.extraFiles.volumeMounts" . | nindent 12 }}
*/}}
{{- define "grader-service.extraFiles.volumeMounts" -}}
{{- range $name, $spec := .Values.extraFiles }}
- name: extra-file-{{ $name }}
  mountPath: {{ $spec.mountPath }}
  subPath: {{ $name }}
  readOnly: true
{{- end }}
{{- end }}

{{/*
Extra-files volumes.
Generates one volume per entry in .Values.extraFiles.
The source can be:
  - `secret`    – mounts a key from an existing Secret
  - `configMap` – mounts a key from an existing ConfigMap
  - `content`   – mounts inline content via a chart-managed ConfigMap
Usage: {{ include "grader-service.extraFiles.volumes" . | nindent 8 }}
*/}}
{{- define "grader-service.extraFiles.volumes" -}}
{{- $fullname := include "grader-service.fullname" . -}}
{{- range $name, $spec := .Values.extraFiles }}
- name: extra-file-{{ $name }}
{{- if $spec.secret }}
  secret:
    secretName: {{ $spec.secret.secretName }}
    {{- if $spec.mode }}
    defaultMode: {{ $spec.mode }}
    {{- end }}
    items:
      - key: {{ $spec.secret.key }}
        path: {{ $name }}
{{- else if $spec.configMap }}
  configMap:
    name: {{ $spec.configMap.name }}
    {{- if $spec.mode }}
    defaultMode: {{ $spec.mode }}
    {{- end }}
    items:
      - key: {{ $spec.configMap.key }}
        path: {{ $name }}
{{- else if $spec.content }}
  configMap:
    name: {{ $fullname }}-extra-files
    {{- if $spec.mode }}
    defaultMode: {{ $spec.mode }}
    {{- end }}
    items:
      - key: {{ $name }}
        path: {{ $name }}
{{- end }}
{{- end }}
{{- end }}
