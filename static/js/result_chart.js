const ctx = document.getElementById("chart")

new Chart(ctx, {

    type: "bar",

    data: {

        labels: labels,

        datasets: [{
            label: "Votes",
            data: values
        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {
                display: false
            }

        }

    }

})