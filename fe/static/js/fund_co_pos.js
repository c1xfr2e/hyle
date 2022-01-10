
let positionTableData;

function openFundHouse(evt, coid) {
  fetch(`/api/fundco/${coid}/position`)
    .then(response => response.json())
    .then(data => {
      positionTableData = data;
      loadTableData(positionTableData);
    });

  if (evt) {
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" w3-safety-blue", "");
    }
    evt.currentTarget.className += " w3-safety-blue";
  }

  resetColumnSortDirections("float_percent");
  resetColumnSortIcons("float_percent", false);
}

function loadTableData(data) {
  const tableBody = document.getElementById("table_data")
  let dataHTML = "";

  for (let p of data) {
    let positionChange = "";
    if (p.enter_count > 0 || p.exit_count > 0) {
      positionChange = `
        <span style="color:#e50000; display:inline-block;">+${p.enter_count}</span>
        <span style="color:#27a64c; display:inline-block; margin-left:4px;">-${p.exit_count}</span>
      `
    }
    dataHTML += `<tr class="w3-hover-2021-illuminating">
      <td>
        <span style="display: inline-block; width: 70px; font-size: 13px;">
          <a href="/stock/${p.code}/fundpos">${p.name}<a>
        </span>
        <span style="display: inline-block; color: gray;">${p.code}</span>
      </td>
      <td>${p.float_percent}</td>
      <td>${p.net_percent}</td>
      <td>${p.funds.length}</td>
      <td>${positionChange}</td>
    </tr>`;
  }

  tableBody.innerHTML = dataHTML;
}

let sortOptions = {
  float_percent: {
    direction: true,
    sortFunc: (dir) => sortNumberColumn("float_percent", dir)
  },
  net_percent: {
    direction: true,
    sortFunc: (dir) => sortNumberColumn("net_percent", dir)
  },
  fund_count: {
    direction: true,
    sortFunc: sortFundCount
  },
  position_change: {
    direction: true,
    sortFunc: sortPositionChange
  },
}

function resetColumnSortDirections(current) {
  for (col in sortOptions) {
    sortOptions[col].direction = true;
  }
  sortOptions[current].direction = false;
}

function resetColumnSortIcons(idToShow, direction) {
  columnSortIcons = document.getElementsByClassName("column-sort-icon");
  for (i = 0; i < columnSortIcons.length; i++) {
    columnSortIcons[i].style.display = "none";
  }

  curIcons = document.getElementById(idToShow).getElementsByClassName("column-sort-icon");
  if (direction) {
    curIcons[0].style.display = "inline";
  } else {
    curIcons[1].style.display = "inline";
  }
}

function sortColumn(evt, columnName) {
  op = sortOptions[columnName];
  op.direction = !op.direction;
  op.sortFunc(op.direction);

  loadTableData(positionTableData);

  resetColumnSortIcons(evt.currentTarget.id, op.direction);
}

function sortNumberColumn(col, dir) {
  positionTableData = positionTableData.sort(
    (p1, p2) => {
      return dir ? p1[col] - p2[col] : p2[col] - p1[col];
    }
  );
}

function sortFundCount(dir) {
  positionTableData = positionTableData.sort(
    (p1, p2) => {
      return dir? p1.funds.length - p2.funds.length : p2.funds.length - p1.funds.length;
    }
  );
}

function sortPositionChange(dir) {
  positionTableData = positionTableData.sort(
    (p1, p2) => {
      v1 = p1.enter_count * 1000 - p1.exit_count;
      v2 = p2.enter_count * 1000 - p2.exit_count;
      return dir? v1 - v2 : v2 - v1;
    }
  );
}
