(function(global) {
    'use strict';

    function renderBabForm(context) {
        if (!context || !context.modalBody) {
            return false;
        }

        var modalBody = context.modalBody;
        var fileType = String(context.fileType || 'WebSeries BAB');
        var createSelectGroup = context.createSelectGroup;
        var createTagGroup = context.createTagGroup;
        var createTagInput = context.createTagInput;
        var getGenerateField = context.getGenerateField;
        var getGenerateTagValues = context.getGenerateTagValues;
        var openMigrationAddressPopup = context.openMigrationAddressPopup;
        var restoreGenerateFormState = context.restoreGenerateFormState;
        var getMigrationAddressRows = context.getMigrationAddressRows;
        var setMigrationAddressRows = context.setMigrationAddressRows;
        var hydrateMigrationAddressRowsFromHiddenField = context.hydrateMigrationAddressRowsFromHiddenField;
        var updateGenerateButtonState = context.updateGenerateButtonState;
        var defaultMigrationRows = Array.isArray(context.defaultMigrationRows) ? context.defaultMigrationRows : [];

        modalBody.classList.add('scrollbarHidden');
        var babLeftColumn = document.createElement('div');
        babLeftColumn.className = 'formColumn';
        babLeftColumn.style.borderRight = '1px solid #555';
        babLeftColumn.style.paddingRight = '15px';
        babLeftColumn.style.display = 'flex';
        babLeftColumn.style.flexDirection = 'column';

        var babBeneficiaryCountHiddenField = document.createElement('input');
        babBeneficiaryCountHiddenField.type = 'hidden';
        babBeneficiaryCountHiddenField.name = 'babBeneficiaryCount';
        babBeneficiaryCountHiddenField.value = '0';
        babLeftColumn.appendChild(babBeneficiaryCountHiddenField);

        var babNotebookHiddenField = document.createElement('input');
        babNotebookHiddenField.type = 'hidden';
        babNotebookHiddenField.name = 'babNotebookEntries';
        babNotebookHiddenField.value = '[]';
        babLeftColumn.appendChild(babNotebookHiddenField);

        var beneficiaryRowGroup = document.createElement('div');
        beneficiaryRowGroup.className = 'formGroup';

        var beneficiaryRowButton = document.createElement('button');
        beneficiaryRowButton.type = 'button';
        beneficiaryRowButton.className = 'generateBtn';
        beneficiaryRowButton.textContent = 'Add a Beneficiary Row';
        beneficiaryRowButton.style.display = 'block';
        beneficiaryRowButton.style.width = 'calc(100% - 20px)';
        beneficiaryRowButton.style.margin = '0 10px';
        beneficiaryRowButton.style.padding = '5px 10px';
        beneficiaryRowButton.style.fontSize = '12px';
        beneficiaryRowButton.style.lineHeight = '1.2';
        beneficiaryRowButton.style.whiteSpace = 'nowrap';

        beneficiaryRowGroup.appendChild(beneficiaryRowButton);
        babLeftColumn.appendChild(beneficiaryRowGroup);

        var babPaymentTypeGroup = createSelectGroup(babLeftColumn, 'Payment Type', 'babPaymentType', [
            { value: '', label: 'Select Payment Type' },
            { value: 'Cash Concentration/Disbursement', label: 'Cash Concentration/Disbursement' },
            { value: 'Wire - Domestic', label: 'Wire - Domestic' },
            { value: 'Wire - International', label: 'Wire - International' }
        ]);
        var babCurrencyGroup = createSelectGroup(babLeftColumn, 'Currency', 'babCurrency', [
            { value: '', label: 'Select Currency' },
            { value: 'AUD', label: 'AUD' },
            { value: 'BRL', label: 'BRL' },
            { value: 'CAD', label: 'CAD' },
            { value: 'CHF', label: 'CHF' },
            { value: 'CNY', label: 'CNY' },
            { value: 'EUR', label: 'EUR' },
            { value: 'GBP', label: 'GBP' },
            { value: 'HKD', label: 'HKD' },
            { value: 'INR', label: 'INR' },
            { value: 'JPY', label: 'JPY' },
            { value: 'NZD', label: 'NZD' },
            { value: 'RUB', label: 'RUB' },
            { value: 'TRY', label: 'TRY' },
            { value: 'USD', label: 'USD' },
            { value: 'ZAR', label: 'ZAR' }
        ]);
        var babPaymentTypeSelect = babPaymentTypeGroup.select;
        var babCurrencySelect = babCurrencyGroup.select;
        var lastBabPaymentType = String(babPaymentTypeSelect.value || '').trim();

        function applyBabCurrencyRules(clearIntlCurrencyOnSwitch) {
            var currentPaymentType = String(babPaymentTypeSelect.value || '').trim();
            var isIntlPayment = currentPaymentType === 'Wire - International';
            if (isIntlPayment) {
                babCurrencySelect.disabled = false;
                if (clearIntlCurrencyOnSwitch) {
                    babCurrencySelect.value = 'GBP';
                }
            } else {
                babCurrencySelect.value = 'USD';
                babCurrencySelect.disabled = true;
            }
            lastBabPaymentType = currentPaymentType;
        }

        function applyBabDefaultBankCodes() {
            var currentPaymentType = String(babPaymentTypeSelect.value || '').trim();
            var bankCodeTypeContainer = document.querySelector('#modalBody .tagInputContainer[data-field-name="babBankCodeType"]');
            var bankCodeContainer = document.querySelector('#modalBody .tagInputContainer[data-field-name="babBankCode"]');
            if (currentPaymentType === 'Cash Concentration/Disbursement') {
                if (bankCodeTypeContainer && typeof bankCodeTypeContainer.setTags === 'function') {
                    bankCodeTypeContainer.setTags(['US-ACH']);
                }
                if (bankCodeContainer && typeof bankCodeContainer.setTags === 'function') {
                    bankCodeContainer.setTags(['021000018']);
                }
            } else if (currentPaymentType === 'Wire - Domestic') {
                if (bankCodeTypeContainer && typeof bankCodeTypeContainer.setTags === 'function') {
                    bankCodeTypeContainer.setTags(['ABA']);
                }
                if (bankCodeContainer && typeof bankCodeContainer.setTags === 'function') {
                    bankCodeContainer.setTags(['021000018']);
                }
            } else if (currentPaymentType === 'Wire - International') {
                if (bankCodeTypeContainer && typeof bankCodeTypeContainer.setTags === 'function') {
                    bankCodeTypeContainer.setTags(['SWIFT']);
                }
                if (bankCodeContainer && typeof bankCodeContainer.setTags === 'function') {
                    bankCodeContainer.setTags(['AACSDE33XXX']);
                }
            }
        }

        babPaymentTypeSelect.addEventListener('change', function() {
            var nextPaymentType = String(babPaymentTypeSelect.value || '').trim();
            var switchedToIntl = nextPaymentType === 'Wire - International' && lastBabPaymentType !== 'Wire - International';
            applyBabCurrencyRules(switchedToIntl);
            applyBabAccountTypeOptions();
            applyBabAccountNumberInputType();
            applyBabDefaultBankCodes();
            updateGenerateButtonState();
        });

        var babAccountTypeGroup = createSelectGroup(babLeftColumn, 'Account Type', 'babAccountType', [
            { value: 'Other', label: 'Other' },
            { value: 'IBAN', label: 'IBAN' }
        ]);
        var babAccountTypeSelect = babAccountTypeGroup.select;

        function applyBabAccountTypeOptions() {
            var currentPaymentType = String(babPaymentTypeSelect.value || '').trim();
            var useCashOptions = currentPaymentType === 'Cash Concentration/Disbursement';
            var useWireDomesticOptions = currentPaymentType === 'Wire - Domestic';
            var options;
            var defaultValue;
            if (useCashOptions) {
                options = [
                    { value: 'Loans', label: 'Loans' },
                    { value: 'Checking', label: 'Checking' },
                    { value: 'Savings', label: 'Savings' }
                ];
                defaultValue = 'Savings';
            } else if (useWireDomesticOptions) {
                options = [
                    { value: 'ABA', label: 'ABA' },
                    { value: 'DDA', label: 'DDA' },
                    { value: 'Other', label: 'Other' },
                    { value: 'SWIFT', label: 'SWIFT' }
                ];
                defaultValue = 'Other';
            } else if (currentPaymentType === 'Wire - International') {
                options = [
                    { value: 'Other', label: 'Other' },
                    { value: 'IBAN', label: 'IBAN' }
                ];
                defaultValue = 'IBAN';
            } else {
                options = [
                    { value: 'Other', label: 'Other' },
                    { value: 'IBAN', label: 'IBAN' }
                ];
                defaultValue = options[0].value;
            }

            var currentValue = String(babAccountTypeSelect.value || '').trim();
            babAccountTypeSelect.innerHTML = '';
            options.forEach(function(optionConfig) {
                var optionEl = document.createElement('option');
                optionEl.value = optionConfig.value;
                optionEl.textContent = optionConfig.label;
                babAccountTypeSelect.appendChild(optionEl);
            });

            var forceDefault = currentPaymentType === 'Wire - International';
            var hasCurrentValue = !forceDefault && options.some(function(optionConfig) {
                return optionConfig.value === currentValue;
            });
            babAccountTypeSelect.value = hasCurrentValue ? currentValue : defaultValue;
        }

        var BAB_IBAN_ACCOUNT_NUMBERS = [
            'DE89370400440532013000',
            'GB29NWBK60161331926819',
            'FR1420041010050500013M02606'
        ];

        var babAccountNumberGroup = document.createElement('div');
        babAccountNumberGroup.className = 'formGroup';
        var babAccountNumberLabel = document.createElement('label');
        babAccountNumberLabel.className = 'formLabel';
        babAccountNumberLabel.textContent = 'Account Number:';
        babAccountNumberGroup.appendChild(babAccountNumberLabel);

        var babAccountNumberTagInput = createTagInput('babAccountNumber', 'Enter account number...', false, { singleValueOnly: true });
        babAccountNumberTagInput.style.flex = '1';

        var babAccountNumberSelect = document.createElement('select');
        babAccountNumberSelect.className = 'formInput';
        babAccountNumberSelect.name = 'babAccountNumber';
        babAccountNumberSelect.style.flex = '1';
        var babAccountNumberPlaceholderOpt = document.createElement('option');
        babAccountNumberPlaceholderOpt.value = '';
        babAccountNumberPlaceholderOpt.textContent = 'Select Account Number';
        babAccountNumberSelect.appendChild(babAccountNumberPlaceholderOpt);
        BAB_IBAN_ACCOUNT_NUMBERS.forEach(function(iban) {
            var opt = document.createElement('option');
            opt.value = iban;
            opt.textContent = iban;
            babAccountNumberSelect.appendChild(opt);
        });
        babAccountNumberSelect.addEventListener('change', function() {
            updateGenerateButtonState();
        });

        babAccountNumberGroup.appendChild(babAccountNumberTagInput);
        babLeftColumn.appendChild(babAccountNumberGroup);

        function applyBabAccountNumberInputType() {
            var isIban = String(babAccountTypeSelect.value || '').trim() === 'IBAN';
            var currentPaymentType = String(babPaymentTypeSelect.value || '').trim();
            if (isIban) {
                if (babAccountNumberGroup.contains(babAccountNumberTagInput)) {
                    babAccountNumberGroup.removeChild(babAccountNumberTagInput);
                }
                if (!babAccountNumberGroup.contains(babAccountNumberSelect)) {
                    babAccountNumberGroup.appendChild(babAccountNumberSelect);
                }
                if (currentPaymentType === 'Wire - International') {
                    babAccountNumberSelect.value = 'GB29NWBK60161331926819';
                }
            } else {
                if (babAccountNumberGroup.contains(babAccountNumberSelect)) {
                    babAccountNumberGroup.removeChild(babAccountNumberSelect);
                }
                if (!babAccountNumberGroup.contains(babAccountNumberTagInput)) {
                    babAccountNumberGroup.appendChild(babAccountNumberTagInput);
                }
            }
        }

        babAccountTypeSelect.addEventListener('change', function() {
            applyBabAccountNumberInputType();
            updateGenerateButtonState();
        });

        createTagGroup(babLeftColumn, 'Bank Code Type', 'babBankCodeType', 'Enter bank code type...', false, { singleValueOnly: true });
        createTagGroup(babLeftColumn, 'Bank Code', 'babBankCode', 'Enter bank code...', false, { singleValueOnly: true });

        var migrationGroup = document.createElement('div');
        migrationGroup.className = 'formGroup';

        var migrationLabel = document.createElement('label');
        migrationLabel.className = 'formLabel';
        migrationLabel.textContent = 'Migration Address Fields:';

        var migrationButton = document.createElement('button');
        migrationButton.type = 'button';
        migrationButton.className = 'generateBtn migrationAddressOpenBtn';
        migrationButton.textContent = 'Open';
        migrationButton.style.flex = '0 0 auto';
        migrationButton.addEventListener('click', function() {
            openMigrationAddressPopup(fileType);
        });

        migrationGroup.appendChild(migrationLabel);
        migrationGroup.appendChild(migrationButton);
        babLeftColumn.appendChild(migrationGroup);

        var migrationHiddenField = document.createElement('input');
        migrationHiddenField.type = 'hidden';
        migrationHiddenField.name = 'migrationAddressFields';
        babLeftColumn.appendChild(migrationHiddenField);

        var babThirdLineCountHiddenField = document.createElement('input');
        babThirdLineCountHiddenField.type = 'hidden';
        babThirdLineCountHiddenField.name = 'babThirdLineCount';
        babThirdLineCountHiddenField.value = '0';
        babLeftColumn.appendChild(babThirdLineCountHiddenField);

        var babMiddleColumn = document.createElement('div');
        babMiddleColumn.className = 'formColumn';
        babMiddleColumn.style.borderRight = 'none';
        babMiddleColumn.style.paddingRight = '0';
        babMiddleColumn.style.gridColumn = '2 / span 2';

        var babNotebookWrap = document.createElement('div');
        babNotebookWrap.style.border = '1px solid #555';
        babNotebookWrap.style.borderRadius = '6px';
        babNotebookWrap.style.minHeight = '260px';
        babNotebookWrap.style.height = 'clamp(260px, 46vh, 360px)';
        babNotebookWrap.style.boxSizing = 'border-box';
        babNotebookWrap.style.padding = '8px';
        babNotebookWrap.style.background = '#1f1f1f';
        babNotebookWrap.style.overflow = 'hidden';

        var babNotebookEditor = document.createElement('textarea');
        babNotebookEditor.className = 'formInput';
        babNotebookEditor.style.width = '100%';
        babNotebookEditor.style.height = '100%';
        babNotebookEditor.style.minHeight = '0';
        babNotebookEditor.style.resize = 'none';
        babNotebookEditor.style.overflowY = 'auto';
        babNotebookEditor.style.border = 'none';
        babNotebookEditor.style.outline = 'none';
        babNotebookEditor.style.background = 'transparent';
        babNotebookEditor.style.color = '#d6e2ff';
        babNotebookEditor.style.fontFamily = 'Consolas, monospace';
        babNotebookEditor.style.fontSize = '13px';
        babNotebookEditor.style.lineHeight = '1.35';
        babNotebookEditor.classList.add('scrollbarHidden');
        babNotebookWrap.appendChild(babNotebookEditor);
        babMiddleColumn.appendChild(babNotebookWrap);

        function parseBabNotebookEntries() {
            try {
                var parsed = JSON.parse(String(babNotebookHiddenField.value || '[]'));
                return Array.isArray(parsed) ? parsed.map(function(value) { return String(value || ''); }) : [];
            } catch (error) {
                return [];
            }
        }

        function setBabNotebookEntries(entries) {
            babNotebookHiddenField.value = JSON.stringify(Array.isArray(entries) ? entries : []);
        }

        function getBabNotebookLines() {
            return String(babNotebookEditor.value || '')
                .split(/\r?\n/)
                .map(function(line) { return String(line || '').trim(); })
                .filter(function(line) { return line; });
        }

        function syncBabNotebookState() {
            var lines = getBabNotebookLines();
            setBabNotebookEntries(lines);

            var lastBeneficiarySequence = 0;
            var lastThirdLineSequence = 0;

            lines.forEach(function(lineText, lineIndex) {
                if (lineText.indexOf('B,') === 0) {
                    var beneMatch = lineText.match(/Bene\s*Contact\s*(\d+)/i);
                    var parsedBeneSequence = beneMatch ? parseInt(beneMatch[1], 10) : (lineIndex + 1);
                    if (Number.isInteger(parsedBeneSequence) && parsedBeneSequence > 0) {
                        lastBeneficiarySequence = parsedBeneSequence;
                    }
                }
                if (lineText.indexOf('A,') === 0) {
                    var beneNameMatch = lineText.match(/BeneName(\d+)/i);
                    var parsedLineSequence = beneNameMatch ? parseInt(beneNameMatch[1], 10) : (lineIndex + 1);
                    if (Number.isInteger(parsedLineSequence) && parsedLineSequence > 0) {
                        lastThirdLineSequence = parsedLineSequence;
                    }
                }
            });

            babBeneficiaryCountHiddenField.value = String(lastBeneficiarySequence);
            babThirdLineCountHiddenField.value = String(lastThirdLineSequence);
            return lines;
        }

        function canAddNextBeneficiaryRow(lines) {
            var sourceLines = Array.isArray(lines) ? lines : getBabNotebookLines();
            var lastBeneficiaryIndex = sourceLines.reduce(function(lastIndex, lineText, index) {
                return lineText.indexOf('B,') === 0 ? index : lastIndex;
            }, -1);
            if (lastBeneficiaryIndex === -1) {
                return true;
            }
            for (var index = lastBeneficiaryIndex + 1; index < sourceLines.length; index += 1) {
                if (sourceLines[index].indexOf('A,') === 0) {
                    return true;
                }
            }
            return false;
        }

        function sanitizeBabMigrationValue(value) {
            var text = String(value || '');
            return text.trim().toLowerCase() === 'null' ? '' : text;
        }

        function getBabSingleTagValue(fieldName) {
            if (fieldName === 'babAccountNumber') {
                var isIban = String(babAccountTypeSelect ? babAccountTypeSelect.value : '').trim() === 'IBAN';
                if (isIban) {
                    return String(babAccountNumberSelect.value || '').trim();
                }
            }
            var values = getGenerateTagValues(fieldName);
            return values.length > 0 ? String(values[0] || '').trim() : '';
        }

        function buildBabSecondLinePreview(beneficiaryIndex) {
            var paymentTypeUpper = String(babPaymentTypeSelect.value || '').trim().toUpperCase();
            var beneReference = paymentTypeUpper === 'NACHA' || paymentTypeUpper === 'BACS' ? 'BeneReference' : '';
            var migrationRows = getMigrationAddressRows(fileType).filter(function(row) {
                return row && typeof row === 'object';
            });
            var rowIndex = migrationRows.length > 0 ? ((beneficiaryIndex - 1) % migrationRows.length) : 0;
            var selectedRow = migrationRows[rowIndex] || { BENE_ADDRESS_1: '', BENE_ADDRESS_2: '' };
            var addr1 = sanitizeBabMigrationValue(selectedRow.BENE_ADDRESS_1);
            var addr2 = sanitizeBabMigrationValue(selectedRow.BENE_ADDRESS_2);
            return 'B,,Bene Contact ' + String(beneficiaryIndex).padStart(2, '0') + ',' + beneReference + ',,,' + addr1 + ',' + addr2 + ',,AK,province,GB,post code,603-501-5470,888888,mg@bt.com,mg1@bt.com,mg2@bt.com';
        }

        function buildBabThirdLinePreview(thirdLineIndex) {
            var paymentType = String(babPaymentTypeSelect.value || '').trim();
            var paymentTypeUpper = paymentType.toUpperCase();
            var isCashConcentration = paymentTypeUpper === 'CASH CONCENTRATION/DISBURSEMENT';
            var paymentTypeMap = {
                'CASH CONCENTRATION/DISBURSEMENT': { payment: 'CCD', clearing: 'NACHA' },
                'WIRE - DOMESTIC': { payment: 'USWIRE', clearing: '' },
                'WIRE - INTERNATIONAL': { payment: 'INT', clearing: '' }
            };
            var resolved = paymentTypeMap[paymentTypeUpper] || { payment: paymentTypeUpper, clearing: '' };
            var beneReference = paymentTypeUpper === 'NACHA' || paymentTypeUpper === 'BACS' ? 'BeneReference' : '';
            var beneName = 'BeneName' + String(thirdLineIndex).padStart(6, '0');
            var currency = String(babCurrencySelect.value || '').trim();
            var accountTypeField = getGenerateField('babAccountType');
            var accountType = String(accountTypeField ? accountTypeField.value : '').trim();
            var accountTypeMap = {
                Savings: 'SV',
                Loans: 'CL',
                Checking: 'DD',
                Checkings: 'DD'
            };
            var resolvedAccountType = isCashConcentration ? (accountTypeMap[accountType] || accountType) : accountType;
            var accountNumber = getBabSingleTagValue('babAccountNumber');
            var bankCodeType = getBabSingleTagValue('babBankCodeType');
            var bankCode = getBabSingleTagValue('babBankCode');
            if (isCashConcentration) {
                return 'A,' + resolved.payment + ',' + resolved.clearing + ',' + beneName + ',' + beneReference + ',,,,,,,' + currency + ',' + resolvedAccountType + ',' + accountNumber + ',' + bankCodeType + ',' + bankCode;
            }
            return 'A,' + resolved.payment + ',' + resolved.clearing + ',' + beneName + ',' + beneReference + ',,,,,,,' + currency + ',' + resolvedAccountType + ',' + accountNumber + ',' + bankCodeType + ',' + bankCode + ',,';
        }

        function renderBabNotebook() {
            var entries = parseBabNotebookEntries();
            babNotebookEditor.value = entries.join('\n');
            babNotebookEditor.scrollTop = babNotebookEditor.scrollHeight;
        }

        function appendBabNotebookLine(lineText) {
            var entries = getBabNotebookLines();
            entries.push(String(lineText || ''));
            babNotebookEditor.value = entries.join('\n');
            syncBabNotebookState();
            babNotebookEditor.scrollTop = babNotebookEditor.scrollHeight;
        }

        babNotebookEditor.addEventListener('input', function() {
            syncBabNotebookState();
            updateGenerateButtonState();
        });

        beneficiaryRowButton.addEventListener('click', function() {
            var notebookLines = syncBabNotebookState();
            if (!canAddNextBeneficiaryRow(notebookLines)) {
                return;
            }
            var parsedCount = parseInt(String(babBeneficiaryCountHiddenField.value || '').trim(), 10);
            var currentCount = Number.isInteger(parsedCount) && parsedCount >= 0 ? parsedCount : 0;
            var nextCount = currentCount + 1;
            appendBabNotebookLine(buildBabSecondLinePreview(nextCount));
            updateGenerateButtonState();
        });

        var addThirdLineGroup = document.createElement('div');
        addThirdLineGroup.className = 'formGroup';
        addThirdLineGroup.style.marginTop = '8px';
        addThirdLineGroup.style.display = 'flex';
        addThirdLineGroup.style.justifyContent = 'flex-end';
        var addThirdLineBtn = document.createElement('button');
        addThirdLineBtn.type = 'button';
        addThirdLineBtn.className = 'generateBtn';
        addThirdLineBtn.textContent = 'Add';
        addThirdLineBtn.style.flex = '0 0 auto';
        addThirdLineBtn.style.alignSelf = 'flex-end';
        addThirdLineBtn.style.padding = '4px 10px';
        addThirdLineBtn.style.fontSize = '12px';
        addThirdLineBtn.style.lineHeight = '1.2';
        addThirdLineBtn.addEventListener('click', function() {
            var notebookLines = syncBabNotebookState();
            var hasBeneficiaryRow = notebookLines.some(function(lineText) {
                return lineText.indexOf('B,') === 0;
            });
            if (!hasBeneficiaryRow) {
                return;
            }
            var paymentType = String(babPaymentTypeSelect.value || '').trim();
            var accountTypeField = getGenerateField('babAccountType');
            var accountType = String(accountTypeField ? accountTypeField.value : '').trim();
            var accountNumber = getBabSingleTagValue('babAccountNumber');
            var bankCodeType = getBabSingleTagValue('babBankCodeType');
            var bankCode = getBabSingleTagValue('babBankCode');
            var currency = String(babCurrencySelect.value || '').trim();
            var needsIntlCurrency = paymentType === 'Wire - International';
            if (!paymentType || !accountType || !accountNumber || !bankCodeType || !bankCode || (needsIntlCurrency && !currency)) {
                alert('Fill all BAB third-line fields before clicking Add.');
                return;
            }
            var parsedCount = parseInt(String(babThirdLineCountHiddenField.value || '').trim(), 10);
            var currentCount = Number.isInteger(parsedCount) && parsedCount >= 0 ? parsedCount : 0;
            var nextCount = currentCount + 1;
            appendBabNotebookLine(buildBabThirdLinePreview(nextCount));
            updateGenerateButtonState();
        });
        addThirdLineGroup.appendChild(addThirdLineBtn);
        babLeftColumn.appendChild(addThirdLineGroup);

        var babRightColumn = document.createElement('div');
        babRightColumn.className = 'formColumn';
        babRightColumn.style.display = 'none';

        modalBody.appendChild(babLeftColumn);
        modalBody.appendChild(babMiddleColumn);
        modalBody.appendChild(babRightColumn);

        var hasRestoredState = restoreGenerateFormState(fileType);
        var currentBabRows = getMigrationAddressRows(fileType);
        var hasBabValues = currentBabRows.some(function(row) {
            return String((row && row.BENE_ADDRESS_1) || '') !== '' || String((row && row.BENE_ADDRESS_2) || '') !== '';
        });

        if (!hasRestoredState || !hasBabValues) {
            setMigrationAddressRows(defaultMigrationRows, fileType);
        }
        if (!String(babBeneficiaryCountHiddenField.value || '').trim()) {
            babBeneficiaryCountHiddenField.value = '0';
        }
        if (getGenerateTagValues('babCurrency').length === 0) {
            var babCurrencyField = getGenerateField('babCurrency');
            if (babCurrencyField) {
                babCurrencyField.value = '';
            }
        }
        var babAccountTypeField = getGenerateField('babAccountType');
        if (babAccountTypeField && !String(babAccountTypeField.value || '').trim()) {
            babAccountTypeField.value = 'Other';
        }
        var parsedThirdLineCount = parseInt(String(babThirdLineCountHiddenField.value || '').trim(), 10);
        if (!Number.isInteger(parsedThirdLineCount) || parsedThirdLineCount < 0) {
            babThirdLineCountHiddenField.value = '0';
        }
        var parsedBeneficiaryCount = parseInt(String(babBeneficiaryCountHiddenField.value || '').trim(), 10);
        if (!Number.isInteger(parsedBeneficiaryCount) || parsedBeneficiaryCount < 0) {
            babBeneficiaryCountHiddenField.value = '0';
        }
        applyBabCurrencyRules(false);
        applyBabAccountTypeOptions();
        applyBabAccountNumberInputType();
        applyBabDefaultBankCodes();
        renderBabNotebook();
        syncBabNotebookState();
        hydrateMigrationAddressRowsFromHiddenField(fileType);
        updateGenerateButtonState();
        return true;
    }

    global.WebSeriesBabUI = {
        renderBabForm: renderBabForm
    };
})(window);



