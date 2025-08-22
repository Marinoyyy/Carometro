document.addEventListener('DOMContentLoaded', function() {
    
    // --- LÓGICA PARA A TELA DE VISUALIZAÇÃO (CARDS) ---
    const selectoresDeSetor = document.querySelectorAll('.setor-selector');

    async function updateOverall(colaboradorId, setor) {
        const overallDisplay = document.getElementById(`overall-${colaboradorId}`);
        if (!overallDisplay) return;

        overallDisplay.style.opacity = '0.5';

        try {
            const response = await fetch(`/api/colaborador/${colaboradorId}/overall/${setor}`);
            if (!response.ok) throw new Error('Erro na API');
            
            const data = await response.json();
            overallDisplay.textContent = data.overall;
        } catch (error) {
            console.error('Falha ao atualizar Overall:', error);
            overallDisplay.textContent = 'Erro';
        } finally {
            overallDisplay.style.opacity = '1';
        }
    }

    selectoresDeSetor.forEach(selector => {
        const colaboradorId = selector.dataset.colaboradorId;
        
        // Calcula o Overall inicial para cada card
        updateOverall(colaboradorId, selector.value);

        // Adiciona o evento de mudança
        selector.addEventListener('change', function() {
            updateOverall(colaboradorId, this.value);
        });
    });


    // --- LÓGICA PARA A TELA DE AVALIAÇÃO ---
    const formsDeAvaliacao = document.querySelectorAll('.evaluation-form');

    formsDeAvaliacao.forEach(form => {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();

            const statusSpan = form.querySelector('.save-status');
            statusSpan.textContent = 'Salvando...';

            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/api/salvar_avaliacao', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                if (!response.ok) throw new Error('Falha ao salvar');

                const result = await response.json();
                statusSpan.textContent = result.mensagem;
                statusSpan.style.color = '#28a745';

            } catch (error) {
                console.error("Erro ao salvar avaliação:", error);
                statusSpan.textContent = 'Erro ao salvar!';
                statusSpan.style.color = '#dc3545';
            } finally {
                setTimeout(() => { statusSpan.textContent = ''; }, 3000);
            }
        });
    });
});