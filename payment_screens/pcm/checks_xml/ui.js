(function(global) {
    'use strict';

    function createSelectGroup(targetColumn, labelText, fieldName, options) {
        var group = document.createElement('div');
        group.className = 'formGroup';

        var label = document.createElement('label');
        label.className = 'formLabel';
        label.textContent = labelText + ':';

        var select = document.createElement('select');
        select.className = 'formInput';
        select.name = fieldName;

        options.forEach(function(opt) {
            var option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.label;
            select.appendChild(option);
        });

        group.appendChild(label);
        group.appendChild(select);
        targetColumn.appendChild(group);
        return { group: group, select: select };
    }

    function renderChecksXmlForm(context) {
        if (!context || !context.modalBody || typeof context.createTagGroup !== 'function' || typeof context.createTagInput !== 'function') {
            return false;
        }

        var modalBody = context.modalBody;
        var createTagGroup = context.createTagGroup;
        var createTagInput = context.createTagInput;
        var updateGenerateButtonState = context.updateGenerateButtonState || function() {};

        var leftColumn = document.createElement('div');
        leftColumn.className = 'formColumn';
        leftColumn.style.borderRight = '1px solid #555';
        leftColumn.style.paddingRight = '15px';

        var middleColumn = document.createElement('div');
        middleColumn.className = 'formColumn';
        middleColumn.style.borderRight = '1px solid #555';
        middleColumn.style.paddingRight = '15px';

        var rightColumn = document.createElement('div');
        rightColumn.className = 'formColumn';

        var fields = [
            { label: 'Batches Quantity', name: 'batchesQuantity', type: 'batchQty' },
            { label: 'Transactions Count', name: 'transactionsCount', type: 'text' },
            {
                label: 'Check Order',
                name: 'checkOrder',
                type: 'dropdown',
                options: [
                    { value: 'None - start from 1000', label: 'None - start from 1000' },
                    { value: 'Ascending', label: 'Ascending' },
                    { value: 'Descending', label: 'Descending' },
                    { value: 'Random', label: 'Random' }
                ]
            },
            {
                label: 'Check App',
                name: 'checkApp',
                type: 'mixed',
                options: [
                    { value: 'Name', label: 'Name' },
                    { value: 'ID', label: 'ID' }
                ]
            },
            { label: 'Check Profiles', name: 'checkProfiles', type: 'text' }
        ];

        var valueMessage = document.createElement('div');
        valueMessage.style.cssText = 'color: #ffffff; font-size: 14px; margin-bottom: 15px; font-style: italic;';
        valueMessage.textContent = 'Only one value is allowed';
        rightColumn.appendChild(valueMessage);

        createTagGroup(rightColumn, 'Client Company', 'clientCompany', 'Enter Client Company', false, { singleValueOnly: true });
        createTagGroup(rightColumn, 'Bank Name', 'bankName', 'Enter Bank Name', false, { singleValueOnly: true });

        createSelectGroup(rightColumn, 'File Name', 'fileName', [
            { value: 'AP', label: 'AP' },
            { value: 'GP', label: 'GP' },
            { value: 'PR', label: 'PR' }
        ]);

        var customRangeMessage = document.createElement('div');
        customRangeMessage.id = 'checkRangeMessage';
        customRangeMessage.style.cssText = 'color: #ffffff; font-size: 14px; margin: 10px 0 6px 0; font-style: italic;';
        customRangeMessage.textContent = "Only applicable on 'Custom Check Order'. You can provide only one value";
        rightColumn.appendChild(customRangeMessage);

        var rangeStartGroup = document.createElement('div');
        rangeStartGroup.id = 'rangeStartGroup';
        rangeStartGroup.className = 'formGroup';
        rangeStartGroup.innerHTML = '<label class="formLabel">Range Start:</label><input type="text" class="formInput" name="rangeStart" placeholder="Enter Range Start" inputmode="numeric" pattern="[0-9]*">';
        rightColumn.appendChild(rangeStartGroup);

        var rangeEndGroup = document.createElement('div');
        rangeEndGroup.id = 'rangeEndGroup';
        rangeEndGroup.className = 'formGroup';
        rangeEndGroup.innerHTML = '<label class="formLabel">Range End:</label><input type="text" class="formInput" name="rangeEnd" placeholder="Enter Range End" inputmode="numeric" pattern="[0-9]*">';
        rightColumn.appendChild(rangeEndGroup);

        fields.forEach(function(field, index) {
            var group = document.createElement('div');
            group.className = 'formGroup';

            var label = document.createElement('label');
            label.className = 'formLabel';
            label.textContent = field.label + ':';
            group.appendChild(label);

            if (field.type === 'batchQty') {
                var batchTagInput = createTagInput(field.name, 'Enter quantity (e.g. 3)', false, { numericPositiveOnly: true, singleValueOnly: true });
                batchTagInput.style.flex = '1';
                group.appendChild(batchTagInput);
            } else if (field.type === 'text') {
                if (field.name === 'transactionsCount' || field.name === 'checkProfiles') {
                    var textTagInput = field.name === 'transactionsCount'
                        ? createTagInput(field.name, 'Enter positive counts...', true, { numericPositiveOnly: true })
                        : createTagInput(field.name, 'Enter ' + field.label + '...', true);
                    textTagInput.style.flex = '1';
                    group.appendChild(textTagInput);
                } else {
                    var textInput = document.createElement('input');
                    textInput.type = 'text';
                    textInput.className = 'formInput';
                    textInput.name = field.name;
                    textInput.placeholder = 'Enter ' + field.label;
                    group.appendChild(textInput);
                }
            } else if (field.type === 'dropdown') {
                var select = document.createElement('select');
                select.className = 'formInput';
                select.name = field.name;
                field.options.forEach(function(opt) {
                    var option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    select.appendChild(option);
                });
                group.appendChild(select);
            } else if (field.type === 'mixed') {
                var container = document.createElement('div');
                container.style.display = 'flex';
                container.style.gap = '10px';
                container.style.flex = '1';
                container.style.minWidth = '0';
                container.style.overflow = 'hidden';

                var mixedSelect = document.createElement('select');
                mixedSelect.className = 'formInput';
                mixedSelect.name = field.name + 'Type';
                mixedSelect.style.flex = '0 0 100px';
                field.options.forEach(function(opt) {
                    var option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    mixedSelect.appendChild(option);
                });

                var mixedTagInput = createTagInput(field.name + 'Value', 'Enter ' + field.label + '...', true);
                mixedTagInput.style.flex = '1';

                container.appendChild(mixedSelect);
                container.appendChild(mixedTagInput);
                group.appendChild(container);
            }

            leftColumn.appendChild(group);

            if (index === 0) {
                var hint = document.createElement('div');
                hint.style.cssText = 'color: #ffffff; font-size: 14px; margin: 15px 0; font-style: italic;';
                hint.textContent = 'You can provide either one or more values separated by commas';
                leftColumn.appendChild(hint);
            }
        });

        modalBody.appendChild(leftColumn);
        modalBody.appendChild(middleColumn);
        modalBody.appendChild(rightColumn);

        var checkOrderSelect = modalBody.querySelector('select[name="checkOrder"]');
        var rangeStartInput = modalBody.querySelector('input[name="rangeStart"]');
        var rangeEndInput = modalBody.querySelector('input[name="rangeEnd"]');

        var numericOnlyHandler = function() {
            this.value = this.value.replace(/\D/g, '');
            updateGenerateButtonState();
        };

        if (rangeStartInput) {
            rangeStartInput.addEventListener('input', numericOnlyHandler);
        }
        if (rangeEndInput) {
            rangeEndInput.addEventListener('input', numericOnlyHandler);
        }

        var toggleCheckRangeFields = function() {
            if (!checkOrderSelect || !customRangeMessage || !rangeStartGroup || !rangeEndGroup) {
                return;
            }

            var showRangeFields = checkOrderSelect.value !== 'None - start from 1000';
            customRangeMessage.style.display = showRangeFields ? 'block' : 'none';
            rangeStartGroup.style.display = showRangeFields ? 'flex' : 'none';
            rangeEndGroup.style.display = showRangeFields ? 'flex' : 'none';

            if (rangeStartInput) {
                rangeStartInput.disabled = !showRangeFields;
                if (!showRangeFields) {
                    rangeStartInput.value = '';
                }
            }
            if (rangeEndInput) {
                rangeEndInput.disabled = !showRangeFields;
                if (!showRangeFields) {
                    rangeEndInput.value = '';
                }
            }

            updateGenerateButtonState();
        };

        if (checkOrderSelect) {
            checkOrderSelect.addEventListener('change', toggleCheckRangeFields);
            toggleCheckRangeFields();
        }

        updateGenerateButtonState();
        return true;
    }

    global.PcmChecksXmlUI = {
        renderChecksXmlForm: renderChecksXmlForm
    };
})(window);

