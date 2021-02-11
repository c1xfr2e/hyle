
let sortDirection = true;

let positionData = [
  {
    name: "贵州茅台",
    percent: 15.0,
    volume_in_float: 0.05,
    fund_count: 100
  },
  {
    name: "柳钢股份",
    percent: 8.0,
    volume_in_float: 3.2,
    fund_count: 2
  },
  {
    name: "金螳螂",
    percent: 12.0,
    volume_in_float: 1.22,
    fund_count: 3
  },
  {
    name: "兔宝宝",
    percent: 18.0,
    volume_in_float: 8.0,
    fund_count: 4
  },
]

window.onload = () => {
  loadTableData(positionData)
}


function loadTableData(positionData) {
  const tableBody = document.getElementById("table_data")
  let dataHTML = "";

  for (let p of positionData) {
    dataHTML += `<tr>
      <td>${p.name}</td>
      <td>${p.percent}%</td>
      <td>${p.volume_in_float}%</td>
      <td>${p.fund_count}</td>
    </tr>`
  }

  tableBody.innerHTML = dataHTML
}

function sortColumn(columnName) {
  const dataType = typeof positionData[0][columnName];
  sortDirection = !sortDirection

  switch (dataType) {
    case "number":
      sortNumberColumn(sortDirection, columnName);
      break;
  }

  loadTableData(positionData)
}

function sortNumberColumn(dir, col) {
  positionData = positionData.sort(
    (p1, p2) => {
      return dir ? p1[col] - p2[col] : p2[col] - p1[col]
    }
  );
}