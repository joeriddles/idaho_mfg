import lunr from 'lunr'

var stdin = process.stdin
var stdout = process.stdout
var buffer = []

stdin.resume()
stdin.setEncoding('utf8')

stdin.on('data', function (data) {
  buffer.push(data)
})

stdin.on('end', function () {
  var documents = JSON.parse(buffer.join(''))

  var idx = lunr(function () {
    this.ref('detail_url')
    this.field('name')
    this.field('description', {
      extractor: (doc) => doc.details.description,
    })
    this.field('products_manufactured', {
      extractor: (doc) => doc.details.products_manufactured,
    })
    this.field('naics_code_primary', {
      extractor: (doc) => doc.details["naics_code_(primary)"],
    })
    this.field('naics_code_secondary', {
      extractor: (doc) => doc.details["naics_code_(secondary)"],
    })
    this.metadataWhitelist = ['position']

    documents.forEach(function (doc) {
      this.add(doc)
    }, this)
  })

  stdout.write(JSON.stringify(idx))
})
