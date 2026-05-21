(function(global) {
    'use strict';

    function renderWireCsvFileForm(context) {
        if (!context || !context.modalBody || typeof context.createTagGroup !== 'function') {
            return false;
        }

        var modalBody = context.modalBody;
        var createTagGroup = context.createTagGroup;
        var setGenerateTagValues = context.setGenerateTagValues || function() {};
        var updateGenerateButtonState = context.updateGenerateButtonState || function() {};
        var requiredAsteriskMarkup = context.requiredAsteriskMarkup || '<span style="color: #ff5555; margin-left: 2px; display: inline-block;">*</span>';

        var csvLeftColumn = document.createElement('div');
        csvLeftColumn.className = 'formColumn';
        csvLeftColumn.style.borderRight = '1px solid #555';
        csvLeftColumn.style.paddingRight = '15px';
        csvLeftColumn.style.display = 'flex';
        csvLeftColumn.style.flexDirection = 'column';

        var csvMiddleColumn = document.createElement('div');
        csvMiddleColumn.className = 'formColumn';
        csvMiddleColumn.style.borderRight = '1px solid #555';
        csvMiddleColumn.style.paddingRight = '15px';
        csvMiddleColumn.style.display = 'flex';
        csvMiddleColumn.style.flexDirection = 'column';
        csvMiddleColumn.style.justifyContent = 'flex-start';
        csvMiddleColumn.style.gap = '0';

        var csvRightColumn = document.createElement('div');
        csvRightColumn.className = 'formColumn';
        csvRightColumn.style.display = 'flex';
        csvRightColumn.style.flexDirection = 'column';
        csvRightColumn.style.justifyContent = 'flex-start';

        var csvRightIntlSection = document.createElement('div');
        csvRightIntlSection.style.display = 'flex';
        csvRightIntlSection.style.flexDirection = 'column';
        csvRightIntlSection.style.gap = '12px';
        csvRightIntlSection.style.opacity = '0.4';
        csvRightIntlSection.style.pointerEvents = 'none';

        var csvRightIntlHeader = document.createElement('div');
        csvRightIntlHeader.className = 'formLabel achSectionLabel';
        csvRightIntlHeader.textContent = 'Wire - International';
        csvRightIntlSection.appendChild(csvRightIntlHeader);

        var csvWireSharedFieldConfigs = [
            { label: 'OriginatorAccountNumber', name: 'originatorAccountNumber', placeholder: 'e.g. 11223344' },
            { label: 'BeneAccountNumber', name: 'beneAccountNumber', placeholder: 'e.g. 12345678 (max 34 chars)', options: { maxTagLength: 34 } },
            { label: 'BeneBankID', name: 'beneBankId', placeholder: 'Enter BeneBankID (9 digits)', options: { numericOnly: true, exactLength: 9, allowDuplicates: true } }
        ];

        var rightIntlInputs = [];

        var csvWireIntlFieldConfigs = [
            { label: 'OriginatorAccountNumber', name: 'intlOriginatorAccountNumber', placeholder: 'e.g. 11223344' },
            { label: 'BeneAccountNumber', name: 'intlBeneAccountNumber', placeholder: 'e.g. 12345678 (max 34 chars)', options: { maxTagLength: 34 } },
            { label: 'BeneBankID', name: 'beneABA', placeholder: 'Enter BeneBankID (9 digits)', options: { numericOnly: true, exactLength: 9, allowDuplicates: true } }
        ];

        csvWireIntlFieldConfigs.forEach(function(cfg) {
            var group = createTagGroup(csvRightIntlSection, cfg.label, cfg.name, cfg.placeholder, true, cfg.options || {}, true);
            var container = group.querySelector('.tagInputContainer');
            if (container) {
                rightIntlInputs.push(container);
            }
        });
        csvRightColumn.appendChild(csvRightIntlSection);

        var csvRightSpacer = document.createElement('div');
        csvRightSpacer.style.flex = '1';
        csvRightColumn.appendChild(csvRightSpacer);

        var csvRightBottomSection = document.createElement('div');
        csvRightBottomSection.style.display = 'flex';
        csvRightBottomSection.style.flexDirection = 'column';
        csvRightBottomSection.style.gap = '12px';

        createTagGroup(csvRightBottomSection, 'Client Company', 'clientCompany', 'Enter client company...', false, { singleValueOnly: true }, true);
        createTagGroup(csvRightBottomSection, 'Bank Name', 'bankName', 'Enter bank name...', false, { singleValueOnly: true }, true);
        csvRightColumn.appendChild(csvRightBottomSection);

        var csvLeftHeaderRow = document.createElement('div');
        csvLeftHeaderRow.style.cssText = 'display: flex; align-items: center; justify-content: space-between; gap: 12px;';

        var csvPaymentHeaderLabel = document.createElement('div');
        csvPaymentHeaderLabel.className = 'formLabel achSectionLabel';
        csvPaymentHeaderLabel.textContent = 'Payment Type';
        csvLeftHeaderRow.appendChild(csvPaymentHeaderLabel);

        var sameForBothRow = document.createElement('div');
        sameForBothRow.style.cssText = 'display: flex; align-items: center; justify-content: flex-end; gap: 8px; width: 100%; padding: 6px 0 0;';
        var sameForBothCheckbox = document.createElement('input');
        sameForBothCheckbox.type = 'checkbox';
        sameForBothCheckbox.id = 'csvSameForBothCheckbox';
        sameForBothCheckbox.name = 'csvSameForBoth';
        sameForBothCheckbox.style.cssText = 'width: 16px; height: 16px; cursor: pointer; flex-shrink: 0;';
        var sameForBothLabel = document.createElement('label');
        sameForBothLabel.htmlFor = 'csvSameForBothCheckbox';
        sameForBothLabel.textContent = 'Same for both';
        sameForBothLabel.style.cssText = 'color: #ffffff; font-size: 14px; cursor: pointer; font-weight: 500; white-space: nowrap;';
        sameForBothRow.appendChild(sameForBothCheckbox);
        sameForBothRow.appendChild(sameForBothLabel);

        csvLeftColumn.appendChild(csvLeftHeaderRow);

        var csvLeftContentWrapper = document.createElement('div');
        csvLeftContentWrapper.style.cssText = 'flex: 1; display: flex; flex-direction: column; justify-content: space-evenly;';
        csvLeftColumn.appendChild(csvLeftContentWrapper);

        var updatingSecondColCheckbox = false;

        var csvDomesticGroup = document.createElement('div');
        csvDomesticGroup.style.cssText = 'display: flex; flex-direction: column;';

        var wireDomesticRow = document.createElement('div');
        wireDomesticRow.style.cssText = 'display: flex; align-items: center; gap: 8px; padding: 6px 0 2px;';
        var wireDomesticCheckbox = document.createElement('input');
        wireDomesticCheckbox.type = 'checkbox';
        wireDomesticCheckbox.id = 'wireDomesticCheckbox';
        wireDomesticCheckbox.name = 'wireDomestic';
        wireDomesticCheckbox.style.cssText = 'width: 16px; height: 16px; cursor: pointer; flex-shrink: 0;';
        var wireDomesticLabel = document.createElement('label');
        wireDomesticLabel.htmlFor = 'wireDomesticCheckbox';
        wireDomesticLabel.textContent = 'Wire - Domestic';
        wireDomesticLabel.style.cssText = 'color: #ffffff; font-size: 14px; cursor: pointer; font-weight: 500;';
        wireDomesticRow.appendChild(wireDomesticCheckbox);
        wireDomesticRow.appendChild(wireDomesticLabel);
        csvDomesticGroup.appendChild(wireDomesticRow);

        var wireCombinedLabel = document.createElement('div');
        wireCombinedLabel.textContent = 'Wire - Domestic & Wire - International';
        wireCombinedLabel.style.cssText = 'color: #ffffff; font-size: 14px; font-weight: 600; padding: 6px 0 12px; display: none;';
        csvDomesticGroup.appendChild(wireCombinedLabel);

        var csvDomesticTxGroup = createTagGroup(csvDomesticGroup, 'Transactions Count', 'wireDomesticTransactionsCount', 'Enter count...', false, { singleValueOnly: true, numericPositiveOnly: true }, true);
        csvDomesticGroup.appendChild(sameForBothRow);
        csvLeftContentWrapper.appendChild(csvDomesticGroup);

        var csvIntlGroup = document.createElement('div');
        csvIntlGroup.style.cssText = 'display: flex; flex-direction: column;';

        var wireInternationalRow = document.createElement('div');
        wireInternationalRow.style.cssText = 'display: flex; align-items: center; gap: 8px; padding: 6px 0 2px;';
        var wireInternationalCheckbox = document.createElement('input');
        wireInternationalCheckbox.type = 'checkbox';
        wireInternationalCheckbox.id = 'wireInternationalCheckbox';
        wireInternationalCheckbox.name = 'wireInternational';
        wireInternationalCheckbox.style.cssText = 'width: 16px; height: 16px; cursor: pointer; flex-shrink: 0;';
        var wireInternationalLabel = document.createElement('label');
        wireInternationalLabel.htmlFor = 'wireInternationalCheckbox';
        wireInternationalLabel.textContent = 'Wire - International';
        wireInternationalLabel.style.cssText = 'color: #ffffff; font-size: 14px; cursor: pointer; font-weight: 500;';
        wireInternationalRow.appendChild(wireInternationalCheckbox);
        wireInternationalRow.appendChild(wireInternationalLabel);
        csvIntlGroup.appendChild(wireInternationalRow);

        var csvIntlTxGroup = createTagGroup(csvIntlGroup, 'Transactions Count', 'wireInternationalTransactionsCount', 'Enter count...', false, { singleValueOnly: true, numericPositiveOnly: true }, true);
        csvLeftContentWrapper.appendChild(csvIntlGroup);

        var csvDomesticTxContainer = csvDomesticGroup.querySelector('[data-field-name="wireDomesticTransactionsCount"]');
        var csvIntlTxContainer = csvIntlGroup.querySelector('[data-field-name="wireInternationalTransactionsCount"]');
        var csvSecondColSameForBothCheckbox;
        var csvDomesticFieldsGroup;
        var csvDomesticHeader;

        function lockTxGroup(group, container, clearValue) {
            if (!group) {
                return;
            }
            group.style.opacity = '0.4';
            group.style.pointerEvents = 'none';
            if (clearValue && container && typeof container.setTags === 'function') {
                container.setTags([]);
            }
        }

        function unlockTxGroup(group) {
            if (!group) {
                return;
            }
            group.style.opacity = '';
            group.style.pointerEvents = '';
        }

        lockTxGroup(csvDomesticTxGroup, csvDomesticTxContainer, false);
        lockTxGroup(csvIntlTxGroup, csvIntlTxContainer, false);

        function getCsvTagValue(container) {
            if (!container || typeof container.getTags !== 'function') {
                return '';
            }
            var tagValues = container.getTags(true);
            return tagValues.length > 0 ? String(tagValues[0]).trim() : '';
        }

        function syncRightIntlSectionState() {
            if (!csvRightIntlSection) {
                return;
            }

            var rightSectionHidden = !!(csvSecondColSameForBothCheckbox && csvSecondColSameForBothCheckbox.checked);
            var shouldEnableRightIntl = !!(sameForBothCheckbox.checked || wireInternationalCheckbox.checked);

            csvRightIntlSection.style.display = rightSectionHidden ? 'none' : 'flex';
            if (rightSectionHidden) {
                csvRightSpacer.style.display = 'none';
                csvRightBottomSection.style.flex = '1';
                csvRightBottomSection.style.justifyContent = 'space-evenly';
                csvRightBottomSection.style.gap = '0';
                rightIntlInputs.forEach(function(container) {
                    if (typeof container.setTags === 'function') {
                        container.setTags([]);
                    }
                });
                return;
            }

            csvRightSpacer.style.display = '';
            csvRightBottomSection.style.flex = '';
            csvRightBottomSection.style.justifyContent = 'flex-start';
            csvRightBottomSection.style.gap = '12px';
            csvRightIntlSection.style.opacity = shouldEnableRightIntl ? '' : '0.4';
            csvRightIntlSection.style.pointerEvents = shouldEnableRightIntl ? '' : 'none';
        }

        function syncSecondColumnHeaderAndFieldsState() {
            var domesticActive = !!wireDomesticCheckbox.checked;
            var internationalActive = !!wireInternationalCheckbox.checked;
            var firstColSameForBothActive = !!sameForBothCheckbox.checked;
            var secondColSameForBothActive = !!(csvSecondColSameForBothCheckbox && csvSecondColSameForBothCheckbox.checked);

            if (csvDomesticHeader) {
                csvDomesticHeader.textContent = secondColSameForBothActive
                    ? 'Wire - Domestic & Wire - International'
                    : 'Wire - Domestic';
                csvDomesticHeader.style.marginBottom = '12px';
            }

            if (!csvDomesticFieldsGroup || !csvDomesticFieldsGroup.style.display || csvDomesticFieldsGroup.style.display === 'none') {
                return;
            }

            var shouldEnableSecondCol = domesticActive || firstColSameForBothActive;
            csvDomesticFieldsGroup.style.opacity = shouldEnableSecondCol ? '' : '0.4';
            csvDomesticFieldsGroup.style.pointerEvents = shouldEnableSecondCol ? '' : 'none';
            if (csvDomesticHeader) {
                csvDomesticHeader.style.opacity = shouldEnableSecondCol ? '' : '0.4';
                csvDomesticHeader.style.pointerEvents = shouldEnableSecondCol ? '' : 'none';
            }

            var shouldEnableSecondColCheckbox = (domesticActive && internationalActive) || firstColSameForBothActive;
            if (csvSecondColSameForBothCheckbox) {
                if (csvSecondColSameForBothCheckbox.checked && !shouldEnableSecondColCheckbox && !updatingSecondColCheckbox) {
                    updatingSecondColCheckbox = true;
                    csvSecondColSameForBothCheckbox.checked = false;
                    csvSecondColSameForBothCheckbox.dispatchEvent(new Event('change', { bubbles: true }));
                    updatingSecondColCheckbox = false;
                }
                csvSecondColSameForBothCheckbox.disabled = !shouldEnableSecondColCheckbox;
                csvSecondColSameForBothCheckbox.style.cursor = shouldEnableSecondColCheckbox ? 'pointer' : 'not-allowed';
                csvSecondColSameForBothCheckbox.style.opacity = shouldEnableSecondColCheckbox ? '1' : '0.5';
                csvSecondColSameForBothCheckbox.style.pointerEvents = 'auto';
                var sameForBothRowElement = csvSecondColSameForBothCheckbox.parentElement;
                if (sameForBothRowElement) {
                    sameForBothRowElement.style.pointerEvents = 'auto';
                    sameForBothRowElement.style.opacity = shouldEnableSecondColCheckbox ? '1' : '0.5';
                }
            }
        }

        function applyCsvSameForBoth(apply) {
            if (apply) {
                wireDomesticRow.style.display = 'none';
                wireCombinedLabel.style.display = '';
                csvIntlGroup.style.display = 'none';
                unlockTxGroup(csvDomesticTxGroup);

                if (csvDomesticFieldsGroup) {
                    csvDomesticFieldsGroup.style.opacity = '';
                    csvDomesticFieldsGroup.style.pointerEvents = '';
                }
                if (csvDomesticHeader) {
                    csvDomesticHeader.style.opacity = '';
                    csvDomesticHeader.style.pointerEvents = '';
                }

                syncRightIntlSectionState();
                syncSecondColumnHeaderAndFieldsState();
                return;
            }

            wireDomesticRow.style.display = '';
            wireCombinedLabel.style.display = 'none';
            csvIntlGroup.style.display = '';

            if (!wireDomesticCheckbox.checked) {
                lockTxGroup(csvDomesticTxGroup, csvDomesticTxContainer, true);
                if (csvDomesticFieldsGroup) {
                    csvDomesticFieldsGroup.style.opacity = '0.4';
                    csvDomesticFieldsGroup.style.pointerEvents = 'none';
                }
                if (csvDomesticHeader) {
                    csvDomesticHeader.style.opacity = '0.4';
                    csvDomesticHeader.style.pointerEvents = 'none';
                }
            }
            if (!wireInternationalCheckbox.checked) {
                lockTxGroup(csvIntlTxGroup, csvIntlTxContainer, true);
            }
            syncRightIntlSectionState();
            syncSecondColumnHeaderAndFieldsState();
        }

        function checkCsvValuesMatch() {
            if (sameForBothCheckbox.checked || !wireDomesticCheckbox.checked || !wireInternationalCheckbox.checked) {
                return;
            }
            var domesticValue = getCsvTagValue(csvDomesticTxContainer);
            var internationalValue = getCsvTagValue(csvIntlTxContainer);
            if (domesticValue && internationalValue && domesticValue === internationalValue) {
                sameForBothCheckbox.checked = true;
                applyCsvSameForBoth(true);
            }
        }

        wireDomesticCheckbox.addEventListener('change', function() {
            if (this.checked) {
                unlockTxGroup(csvDomesticTxGroup);
            } else {
                if (sameForBothCheckbox.checked) {
                    sameForBothCheckbox.checked = false;
                    applyCsvSameForBoth(false);
                }
                lockTxGroup(csvDomesticTxGroup, csvDomesticTxContainer, true);
            }
            syncSecondColumnHeaderAndFieldsState();
        });

        wireInternationalCheckbox.addEventListener('change', function() {
            if (this.checked) {
                unlockTxGroup(csvIntlTxGroup);
                setGenerateTagValues('beneABA', ['053000196']);
            } else {
                lockTxGroup(csvIntlTxGroup, csvIntlTxContainer, true);
                rightIntlInputs.forEach(function(container) {
                    if (typeof container.setTags === 'function') {
                        container.setTags([]);
                    }
                });
            }
            syncRightIntlSectionState();
            syncSecondColumnHeaderAndFieldsState();
        });

        if (csvDomesticTxContainer && csvIntlTxContainer) {
            var csvTagObserver = new MutationObserver(function() {
                checkCsvValuesMatch();
            });
            csvTagObserver.observe(csvDomesticTxContainer, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-tags'] });
            csvTagObserver.observe(csvIntlTxContainer, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-tags'] });
        }

        sameForBothCheckbox.addEventListener('change', function() {
            applyCsvSameForBoth(this.checked);
            if (this.checked && csvDomesticTxContainer && csvIntlTxContainer) {
                var domesticTags = typeof csvDomesticTxContainer.getTags === 'function'
                    ? csvDomesticTxContainer.getTags(true)
                    : [];
                setGenerateTagValues('wireInternationalTransactionsCount', domesticTags);
            }
        });

        var csvFutureBusinessDateGroup = document.createElement('div');
        csvFutureBusinessDateGroup.className = 'formGroup';
        var csvFutureBusinessDateLabel = document.createElement('label');
        csvFutureBusinessDateLabel.className = 'formLabel';
        csvFutureBusinessDateLabel.innerHTML = '<span style="white-space: nowrap;">FutureBusinessDate:' + requiredAsteriskMarkup + '</span>';
        var csvFutureBusinessDateInput = document.createElement('input');
        csvFutureBusinessDateInput.type = 'date';
        csvFutureBusinessDateInput.className = 'formInput';
        csvFutureBusinessDateInput.name = 'futureBusinessDate';
        var today = new Date();
        csvFutureBusinessDateInput.min = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');

        var csvFutureBusinessDateInputWrap = document.createElement('div');
        csvFutureBusinessDateInputWrap.className = 'dateInputWithIcon';

        var csvFutureBusinessDateIconBtn = document.createElement('button');
        csvFutureBusinessDateIconBtn.type = 'button';
        csvFutureBusinessDateIconBtn.className = 'datePickerIconBtn';
        csvFutureBusinessDateIconBtn.textContent = '📅';
        csvFutureBusinessDateIconBtn.title = 'Open calendar';
        csvFutureBusinessDateIconBtn.setAttribute('aria-label', 'Open calendar');
        csvFutureBusinessDateIconBtn.addEventListener('click', function() {
            if (typeof csvFutureBusinessDateInput.showPicker === 'function') {
                csvFutureBusinessDateInput.showPicker();
            } else {
                csvFutureBusinessDateInput.focus();
                csvFutureBusinessDateInput.click();
            }
        });

        csvFutureBusinessDateInputWrap.appendChild(csvFutureBusinessDateInput);
        csvFutureBusinessDateInputWrap.appendChild(csvFutureBusinessDateIconBtn);
        csvFutureBusinessDateGroup.appendChild(csvFutureBusinessDateLabel);
        csvFutureBusinessDateGroup.appendChild(csvFutureBusinessDateInputWrap);
        csvFutureBusinessDateGroup.style.marginTop = '16px';
        csvMiddleColumn.appendChild(csvFutureBusinessDateGroup);

        var csvDomesticFieldsGap = document.createElement('div');
        csvDomesticFieldsGap.style.height = '96px';
        csvMiddleColumn.appendChild(csvDomesticFieldsGap);

        csvDomesticHeader = document.createElement('div');
        csvDomesticHeader.className = 'formLabel achSectionLabel';
        csvDomesticHeader.textContent = 'Wire - Domestic';
        csvDomesticHeader.style.marginTop = '2px';
        csvDomesticHeader.style.opacity = '0.4';
        csvDomesticHeader.style.pointerEvents = 'none';
        csvMiddleColumn.appendChild(csvDomesticHeader);

        csvDomesticFieldsGroup = document.createElement('div');
        csvDomesticFieldsGroup.style.display = 'flex';
        csvDomesticFieldsGroup.style.flexDirection = 'column';
        csvDomesticFieldsGroup.style.gap = '16px';
        csvDomesticFieldsGroup.style.opacity = '0.4';
        csvDomesticFieldsGroup.style.pointerEvents = 'none';

        var csvOriginatorAccountGroup = createTagGroup(csvDomesticFieldsGroup, csvWireSharedFieldConfigs[0].label, csvWireSharedFieldConfigs[0].name, csvWireSharedFieldConfigs[0].placeholder, true, {}, true);
        var csvBeneAccountGroup = createTagGroup(csvDomesticFieldsGroup, csvWireSharedFieldConfigs[1].label, csvWireSharedFieldConfigs[1].name, csvWireSharedFieldConfigs[1].placeholder, true, csvWireSharedFieldConfigs[1].options, true);
        var csvBeneBankIdGroup = createTagGroup(csvDomesticFieldsGroup, csvWireSharedFieldConfigs[2].label, csvWireSharedFieldConfigs[2].name, csvWireSharedFieldConfigs[2].placeholder, true, csvWireSharedFieldConfigs[2].options, true);

        var csvSecondColSameForBothRow = document.createElement('div');
        csvSecondColSameForBothRow.style.cssText = 'display: flex; align-items: center; justify-content: flex-end; gap: 8px; width: 100%; padding: 4px 0 0;';
        csvSecondColSameForBothCheckbox = document.createElement('input');
        csvSecondColSameForBothCheckbox.type = 'checkbox';
        csvSecondColSameForBothCheckbox.id = 'csvSecondColSameForBothCheckbox';
        csvSecondColSameForBothCheckbox.name = 'csvSecondColSameForBoth';
        csvSecondColSameForBothCheckbox.style.cssText = 'width: 16px; height: 16px; cursor: pointer; flex-shrink: 0;';
        var csvSecondColSameForBothLabel = document.createElement('label');
        csvSecondColSameForBothLabel.htmlFor = 'csvSecondColSameForBothCheckbox';
        csvSecondColSameForBothLabel.textContent = 'same for both';
        csvSecondColSameForBothLabel.style.cssText = 'color: #ffffff; font-size: 14px; cursor: pointer; font-weight: 500; white-space: nowrap;';
        csvSecondColSameForBothRow.appendChild(csvSecondColSameForBothCheckbox);
        csvSecondColSameForBothRow.appendChild(csvSecondColSameForBothLabel);
        csvDomesticFieldsGroup.appendChild(csvSecondColSameForBothRow);
        csvMiddleColumn.appendChild(csvDomesticFieldsGroup);

        function updateMiddleColumnLayout(sameForBothActive) {
            if (sameForBothActive) {
                csvDomesticFieldsGap.style.display = 'none';
                csvDomesticHeader.style.display = 'none';
                csvDomesticFieldsGroup.style.display = 'none';
                csvDomesticFieldsGroup.style.opacity = '1';
                csvDomesticFieldsGroup.style.pointerEvents = 'auto';
                csvFutureBusinessDateGroup.style.marginTop = '';
                csvMiddleColumn.style.justifyContent = 'space-evenly';
                csvMiddleColumn.appendChild(csvOriginatorAccountGroup);
                csvMiddleColumn.appendChild(csvBeneAccountGroup);
                csvMiddleColumn.appendChild(csvBeneBankIdGroup);
                return;
            }

            if (csvOriginatorAccountGroup.parentElement === csvMiddleColumn) {
                csvDomesticFieldsGroup.appendChild(csvOriginatorAccountGroup);
            }
            if (csvBeneAccountGroup.parentElement === csvMiddleColumn) {
                csvDomesticFieldsGroup.appendChild(csvBeneAccountGroup);
            }
            if (csvBeneBankIdGroup.parentElement === csvMiddleColumn) {
                csvDomesticFieldsGroup.appendChild(csvBeneBankIdGroup);
            }

            csvDomesticFieldsGap.style.display = '';
            csvDomesticHeader.style.display = '';
            csvDomesticFieldsGroup.style.display = 'flex';
            csvFutureBusinessDateGroup.style.marginTop = '16px';
            csvMiddleColumn.style.justifyContent = 'flex-start';
            csvDomesticFieldsGroup.style.opacity = '0.4';
            csvDomesticFieldsGroup.style.pointerEvents = 'none';
        }

        csvSecondColSameForBothCheckbox.addEventListener('change', function() {
            updateMiddleColumnLayout(this.checked);
            syncSecondColumnHeaderAndFieldsState();
            syncRightIntlSectionState();
        });

        modalBody.appendChild(csvLeftColumn);
        modalBody.appendChild(csvMiddleColumn);
        modalBody.appendChild(csvRightColumn);

        var wirePaymentTypeInput = document.createElement('input');
        wirePaymentTypeInput.type = 'hidden';
        wirePaymentTypeInput.name = 'wirePaymentType';
        wirePaymentTypeInput.value = '';
        modalBody.appendChild(wirePaymentTypeInput);

        var wireFirstColSameForBothInput = document.createElement('input');
        wireFirstColSameForBothInput.type = 'hidden';
        wireFirstColSameForBothInput.name = 'wireFirstColSameForBoth';
        wireFirstColSameForBothInput.value = 'false';
        modalBody.appendChild(wireFirstColSameForBothInput);

        var wireSecondColSameForBothInput = document.createElement('input');
        wireSecondColSameForBothInput.type = 'hidden';
        wireSecondColSameForBothInput.name = 'wireSecondColSameForBoth';
        wireSecondColSameForBothInput.value = 'false';
        modalBody.appendChild(wireSecondColSameForBothInput);

        function updateWirePaymentType() {
            var domesticChecked = wireDomesticCheckbox.checked;
            var internationalChecked = wireInternationalCheckbox.checked || sameForBothCheckbox.checked;
            if (domesticChecked && internationalChecked) {
                wirePaymentTypeInput.value = 'both';
            } else if (internationalChecked) {
                wirePaymentTypeInput.value = 'international';
            } else if (domesticChecked) {
                wirePaymentTypeInput.value = 'domestic';
            } else {
                wirePaymentTypeInput.value = '';
            }
            wireFirstColSameForBothInput.value = sameForBothCheckbox.checked ? 'true' : 'false';
            wireSecondColSameForBothInput.value = csvSecondColSameForBothCheckbox && csvSecondColSameForBothCheckbox.checked ? 'true' : 'false';
        }

        wireDomesticCheckbox.addEventListener('change', updateWirePaymentType);
        wireInternationalCheckbox.addEventListener('change', updateWirePaymentType);
        sameForBothCheckbox.addEventListener('change', updateWirePaymentType);
        csvSecondColSameForBothCheckbox.addEventListener('change', updateWirePaymentType);

        setGenerateTagValues('beneBankId', ['053000196']);
        setGenerateTagValues('beneABA', ['053000196']);

        var beneBankIdInputs = modalBody.querySelectorAll('input[name="beneBankId"], textarea[name="beneBankId"]');
        beneBankIdInputs.forEach(function(abaInput) {
            if (abaInput.dataset.abaValidationAdded) {
                return;
            }
            abaInput.dataset.abaValidationAdded = 'true';
            abaInput.addEventListener('keydown', function(event) {
                if (!/[\d,\b\t\r\n]/.test(event.key) && !/[0-9]/.test(event.key) &&
                    ['Backspace', 'Delete', 'Tab', 'Enter', ',', 'Comma', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].indexOf(event.key) === -1) {
                    event.preventDefault();
                }
            });
            abaInput.addEventListener('input', function() {
                this.value = String(this.value || '').replace(/[^\d,]/g, '');
            });
        });

        syncSecondColumnHeaderAndFieldsState();
        syncRightIntlSectionState();
        updateWirePaymentType();
        updateGenerateButtonState();
        return true;
    }

    global.PcmWireCsvFileUI = {
        renderWireCsvFileForm: renderWireCsvFileForm
    };
})(window);

