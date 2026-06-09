(function(global) {
    'use strict';

    var MULTI_VALUE_FIELDS = {
        transactionsCount: true,
        achCompIds: true,
        achCompNames: true,
        abas: true,
        payeeIds: true,
        payeeLookupElements: true,
        payeeEmails: true,
        esendAppValue: true,
        esendProfileKeys: true
    };

    var previewState = {
        token: '',
        payloadSignature: ''
    };

    function resolveElement(reference) {
        if (!reference) {
            return null;
        }
        if (typeof reference === 'string') {
            return document.getElementById(reference) || document.querySelector(reference);
        }
        return reference;
    }

    function splitDelimitedValues(rawValue) {
        return String(rawValue || '')
            .split(/[\n,]+/)
            .map(function(value) {
                return String(value || '').trim();
            })
            .filter(Boolean);
    }

    function getField(form, name) {
        return form ? form.querySelector('[name="' + name + '"]') : null;
    }

    function getContainer(form, name) {
        return form ? form.querySelector('[data-field-container="' + name + '"]') : null;
    }

    function getErrorNode(container) {
        return container ? container.querySelector('.fieldError') : null;
    }

    function getSingleValue(form, name) {
        var field = getField(form, name);
        return field ? String(field.value || '').trim() : '';
    }

    function getMultiValues(form, name) {
        return splitDelimitedValues(getSingleValue(form, name));
    }

    function setFieldError(form, name, message) {
        var container = getContainer(form, name);
        var field = getField(form, name);
        var errorNode = getErrorNode(container);
        if (field) {
            field.classList.add('is-invalid');
            field.setAttribute('aria-invalid', 'true');
        }
        if (errorNode) {
            errorNode.textContent = message;
            errorNode.classList.add('is-visible');
        }
    }

    function clearFieldError(form, name) {
        var container = getContainer(form, name);
        var field = getField(form, name);
        var errorNode = getErrorNode(container);
        if (field) {
            field.classList.remove('is-invalid');
            field.removeAttribute('aria-invalid');
        }
        if (errorNode) {
            errorNode.textContent = '';
            errorNode.classList.remove('is-visible');
        }
    }

    function clearAllFieldErrors(form) {
        if (!form) {
            return;
        }
        Array.prototype.forEach.call(form.querySelectorAll('[data-field-container]'), function(container) {
            var name = container.getAttribute('data-field-container');
            if (name) {
                clearFieldError(form, name);
            }
        });
    }

    function showSummary(summary, errors) {
        if (!summary) {
            return;
        }
        if (!errors || errors.length === 0) {
            summary.innerHTML = '';
            summary.classList.remove('is-visible', 'is-error');
            return;
        }
        var items = errors.map(function(error) {
            return '<li>' + escapeHtml(error) + '</li>';
        }).join('');
        summary.innerHTML = '<strong>Please fix the following issues:</strong><ul>' + items + '</ul>';
        summary.classList.add('is-visible', 'is-error');
    }

    function showMessage(messageBox, message, isSuccess) {
        if (!messageBox) {
            return;
        }
        if (!message) {
            messageBox.textContent = '';
            messageBox.classList.remove('is-visible', 'is-success', 'is-error');
            return;
        }
        messageBox.textContent = message;
        messageBox.classList.add('is-visible');
        messageBox.classList.toggle('is-success', Boolean(isSuccess));
        messageBox.classList.toggle('is-error', !isSuccess);
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function isEsendEnabled(form) {
        var optionsValue = getSingleValue(form, 'options');
        return optionsValue === 'ACH & ESend' || optionsValue === 'ESend_Only';
    }

    function toggleEsendState(form) {
        var esendActive = isEsendEnabled(form);
        Array.prototype.forEach.call(document.querySelectorAll('[data-esend-section]'), function(section) {
            section.setAttribute('data-esend-active', esendActive ? 'true' : 'false');
        });
        return esendActive;
    }

    function normalizeListPayload(values) {
        return values.join(',');
    }

    function buildPayload(form) {
        var payload = {
            fileType: 'ACH NACHA XML',
            usePreSeedData: false,
            __tagValues: {}
        };

        Array.prototype.forEach.call(form.querySelectorAll('[name]'), function(field) {
            var name = field.name;
            if (!name) {
                return;
            }
            if (MULTI_VALUE_FIELDS[name]) {
                var values = getMultiValues(form, name);
                payload.__tagValues[name] = values;
                payload[name] = normalizeListPayload(values);
            } else {
                payload[name] = String(field.value || '').trim();
            }
        });

        return payload;
    }

    function parsePositiveInteger(value) {
        if (!/^\d+$/.test(String(value || '').trim())) {
            return null;
        }
        var parsed = parseInt(String(value).trim(), 10);
        return parsed > 0 ? parsed : null;
    }

    function validateForm(form, options) {
        var summary = options && options.summary ? options.summary : null;
        var errors = [];
        var seenFieldErrors = {};
        var payload;

        function addError(name, message) {
            errors.push(message);
            if (name && !seenFieldErrors[name]) {
                setFieldError(form, name, message);
                seenFieldErrors[name] = true;
            }
        }

        clearAllFieldErrors(form);

        var batchesQuantityRaw = getSingleValue(form, 'batchesQuantity');
        var batchCount = parsePositiveInteger(batchesQuantityRaw);
        if (!batchCount) {
            addError('batchesQuantity', 'Batches Quantity must be a numeric value greater than 0.');
        }

        var transactionsCounts = getMultiValues(form, 'transactionsCount');
        if (transactionsCounts.length === 0) {
            addError('transactionsCount', 'Transactions Count is mandatory and must contain at least one value greater than 0.');
        } else {
            var invalidTransactions = transactionsCounts.filter(function(value) {
                return parsePositiveInteger(value) === null;
            });
            if (invalidTransactions.length > 0) {
                addError('transactionsCount', 'Transactions Count accepts only numeric values greater than 0.');
            } else if (batchCount && transactionsCounts.length > 1 && transactionsCounts.length !== batchCount) {
                addError('transactionsCount', 'Transactions Count must contain either one value for all batches or exactly one value per batch.');
            }
        }

        if (!getSingleValue(form, 'type')) {
            addError('type', 'Type is mandatory.');
        }

        if (!getSingleValue(form, 'options')) {
            addError('options', 'Options is mandatory.');
        }

        var achCompIds = getMultiValues(form, 'achCompIds');
        if (achCompIds.length === 0) {
            addError('achCompIds', 'ACH Comp IDs are mandatory.');
        }

        var achCompNames = getMultiValues(form, 'achCompNames');
        if (achCompNames.length === 0) {
            addError('achCompNames', 'ACH Comp Names are mandatory.');
        }

        if (achCompIds.length > 0 && achCompNames.length > 0 && achCompIds.length !== achCompNames.length) {
            addError('achCompNames', 'ACH Comp IDs and ACH Comp Names must have the same number of values.');
        }

        if (batchCount) {
            if (achCompIds.length > 1 && achCompIds.length !== batchCount) {
                addError('achCompIds', 'ACH Comp IDs must contain either one value for all batches or exactly one value per batch.');
            }
            if (achCompNames.length > 1 && achCompNames.length !== batchCount) {
                addError('achCompNames', 'ACH Comp Names must contain either one value for all batches or exactly one value per batch.');
            }
        }

        if (!getSingleValue(form, 'clientCompany')) {
            addError('clientCompany', 'Client Company is mandatory.');
        }

        var abas = getMultiValues(form, 'abas');
        if (abas.length === 0) {
            addError('abas', 'ABAs are mandatory.');
        } else {
            var invalidAbas = abas.filter(function(value) {
                return !/^\d{9}$/.test(String(value || '').trim());
            });
            if (invalidAbas.length > 0) {
                addError('abas', 'Each ABA must be exactly 9 digits.');
            }
        }

        if (!getSingleValue(form, 'bankName')) {
            addError('bankName', 'Bank Name is mandatory.');
        }

        var esendEnabled = toggleEsendState(form);
        if (esendEnabled) {
            var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            var payeeEmails = getMultiValues(form, 'payeeEmails');
            if (payeeEmails.length === 0) {
                addError('payeeEmails', 'Payee Emails are mandatory when ESend is enabled.');
            } else if (payeeEmails.some(function(email) { return !emailPattern.test(email); })) {
                addError('payeeEmails', 'Payee Emails must be valid email addresses when ESend is enabled.');
            }

            var esendAppValues = getMultiValues(form, 'esendAppValue');
            if (esendAppValues.length === 0) {
                addError('esendAppValue', 'ESend App Value is mandatory when ESend is enabled.');
            } else if (batchCount && esendAppValues.length > 1 && esendAppValues.length !== batchCount) {
                addError('esendAppValue', 'ESend App Value must contain either one value for all batches or exactly one value per batch.');
            }

            var esendProfileKeys = getMultiValues(form, 'esendProfileKeys');
            if (esendProfileKeys.length === 0) {
                addError('esendProfileKeys', 'ESend Profile Keys are mandatory when ESend is enabled.');
            } else if (batchCount && esendProfileKeys.length > 1 && esendProfileKeys.length !== batchCount) {
                addError('esendProfileKeys', 'ESend Profile Keys must contain either one value for all batches or exactly one value per batch.');
            }
        }

        payload = buildPayload(form);
        showSummary(summary, errors);

        return {
            valid: errors.length === 0,
            errors: errors,
            payload: payload
        };
    }

    function openPreview(previewOverlay, previewTitle, previewContent, title, content) {
        if (!previewOverlay || !previewTitle || !previewContent) {
            return;
        }
        previewTitle.textContent = title || 'ACH NACHA XML Preview';
        previewContent.textContent = content || '';
        previewOverlay.classList.add('is-visible');
        previewOverlay.setAttribute('aria-hidden', 'false');
    }

    function closePreview(previewOverlay) {
        if (!previewOverlay) {
            return;
        }
        previewOverlay.classList.remove('is-visible');
        previewOverlay.setAttribute('aria-hidden', 'true');
    }

    function resetDownloadPanel(downloadPanel, downloadLink, downloadMessage) {
        if (downloadPanel) {
            downloadPanel.classList.remove('is-visible', 'is-success');
        }
        if (downloadLink) {
            downloadLink.removeAttribute('href');
            downloadLink.removeAttribute('download');
        }
        if (downloadMessage) {
            downloadMessage.textContent = '';
        }
    }

    function showDownloadPanel(downloadPanel, downloadLink, downloadMessage, filename, url) {
        if (!downloadPanel || !downloadLink || !downloadMessage) {
            return;
        }
        downloadPanel.classList.add('is-visible', 'is-success');
        downloadMessage.textContent = 'File generated successfully: ' + filename;
        downloadLink.href = url;
        downloadLink.download = filename;
    }

    function bindForm(config) {
        var form = resolveElement(config && config.form);
        var summary = resolveElement(config && config.summary);
        var messageBox = resolveElement(config && config.messageBox);
        var previewButton = resolveElement(config && config.previewButton);
        var validateButton = resolveElement(config && config.validateButton);
        var previewOverlay = resolveElement(config && config.previewOverlay);
        var previewTitle = resolveElement(config && config.previewTitle);
        var previewContent = resolveElement(config && config.previewContent);
        var closePreviewButton = resolveElement(config && config.closePreviewButton);
        var downloadPanel = resolveElement(config && config.downloadPanel);
        var downloadMessage = resolveElement(config && config.downloadMessage);
        var downloadLink = resolveElement(config && config.downloadLink);
        var hasValidatedOnce = false;

        if (!form) {
            return null;
        }

        function revalidateIfNeeded() {
            toggleEsendState(form);
            if (hasValidatedOnce) {
                validateForm(form, { summary: summary });
            }
        }

        function getPayloadSignature(payload) {
            var cloned = JSON.parse(JSON.stringify(payload || {}));
            delete cloned.achNachaXmlPreviewToken;
            return JSON.stringify(cloned);
        }

        function resetPreviewState() {
            previewState.token = '';
            previewState.payloadSignature = '';
        }

        Array.prototype.forEach.call(form.querySelectorAll('input, select, textarea'), function(field) {
            var eventName = field.tagName === 'SELECT' ? 'change' : 'input';
            field.addEventListener(eventName, function() {
                showMessage(messageBox, '', true);
                resetDownloadPanel(downloadPanel, downloadLink, downloadMessage);
                revalidateIfNeeded();
            });
            if (field.tagName !== 'SELECT') {
                field.addEventListener('blur', function() {
                    if (hasValidatedOnce) {
                        validateForm(form, { summary: summary });
                    }
                });
            }
        });

        form.addEventListener('reset', function() {
            resetPreviewState();
            window.setTimeout(function() {
                hasValidatedOnce = false;
                clearAllFieldErrors(form);
                showSummary(summary, []);
                showMessage(messageBox, '', true);
                resetDownloadPanel(downloadPanel, downloadLink, downloadMessage);
                toggleEsendState(form);
            }, 0);
        });

        if (validateButton) {
            validateButton.addEventListener('click', function() {
                hasValidatedOnce = true;
                var result = validateForm(form, { summary: summary });
                showMessage(messageBox, result.valid ? 'Validation passed.' : 'Validation failed. Review the issues below.', result.valid);
            });
        }

        if (previewButton) {
            previewButton.addEventListener('click', async function() {
                hasValidatedOnce = true;
                resetDownloadPanel(downloadPanel, downloadLink, downloadMessage);
                var result = validateForm(form, { summary: summary });
                if (!result.valid) {
                    showMessage(messageBox, 'Preview blocked until validation issues are fixed.', false);
                    return;
                }
                if (!global.PcmAchNachaXmlActions || typeof global.PcmAchNachaXmlActions.previewAchNachaXmlFile !== 'function') {
                    showMessage(messageBox, 'Preview action is not available. `actions.js` is not loaded.', false);
                    return;
                }
                showMessage(messageBox, 'Loading preview…', true);
                await global.PcmAchNachaXmlActions.previewAchNachaXmlFile({
                    data: result.payload,
                    fileType: 'ACH NACHA XML',
                    addMessage: function(message, isSuccess) {
                        showMessage(messageBox, message, isSuccess !== false);
                    },
                    showGeneratePreviewModal: function(title, content) {
                        openPreview(previewOverlay, previewTitle, previewContent, title, content);
                    },
                    getGeneratePreviewTitle: function() {
                        return 'ACH NACHA XML Preview';
                    },
                    getAchNachaXmlPreviewSignature: getPayloadSignature,
                    setAchNachaXmlPreviewState: function(nextState) {
                        previewState.token = nextState && nextState.token ? nextState.token : '';
                        previewState.payloadSignature = nextState && nextState.payloadSignature ? nextState.payloadSignature : '';
                    },
                    resetAchNachaXmlPreviewState: resetPreviewState
                });
            });
        }

        if (closePreviewButton) {
            closePreviewButton.addEventListener('click', function() {
                closePreview(previewOverlay);
            });
        }

        if (previewOverlay) {
            previewOverlay.addEventListener('click', function(event) {
                if (event.target === previewOverlay) {
                    closePreview(previewOverlay);
                }
            });
        }

        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            hasValidatedOnce = true;
            var result = validateForm(form, { summary: summary });
            if (!result.valid) {
                showMessage(messageBox, 'Generate blocked until validation issues are fixed.', false);
                return;
            }
            if (!global.PcmAchNachaXmlActions || typeof global.PcmAchNachaXmlActions.generateAchNachaXmlFile !== 'function') {
                showMessage(messageBox, 'Generate action is not available. `actions.js` is not loaded.', false);
                return;
            }
            showMessage(messageBox, 'Generating file…', true);
            await global.PcmAchNachaXmlActions.generateAchNachaXmlFile({
                data: result.payload,
                formsPayload: [result.payload],
                addMessage: function(message, isSuccess) {
                    showMessage(messageBox, message, isSuccess !== false);
                },
                showSuccessPopup: function(filename, url) {
                    showMessage(messageBox, 'File generated successfully.', true);
                    showDownloadPanel(downloadPanel, downloadLink, downloadMessage, filename, url);
                },
                getAchNachaXmlPreviewState: function() {
                    return {
                        token: previewState.token,
                        payloadSignature: previewState.payloadSignature
                    };
                },
                getAchNachaXmlPreviewSignature: getPayloadSignature,
                resetAchNachaXmlPreviewState: resetPreviewState
            });
        });

        toggleEsendState(form);

        return {
            validate: function() {
                hasValidatedOnce = true;
                return validateForm(form, { summary: summary });
            },
            getPayload: function() {
                return buildPayload(form);
            },
            resetPreviewState: resetPreviewState,
            closePreview: function() {
                closePreview(previewOverlay);
            }
        };
    }

    global.PcmAchNachaXmlValidation = {
        bindForm: bindForm,
        validateForm: validateForm,
        buildPayload: buildPayload,
        splitDelimitedValues: splitDelimitedValues
    };
})(window);


