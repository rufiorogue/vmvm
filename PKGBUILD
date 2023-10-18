pkgname=vmvm
pkgver=0.1.0
pkgrel=1
pkgdesc="QEMU wrapper and shell"
arch=('any')
url="https://github.com/roovio/vmvm"
license=('MIT')
depends=('python' 'python-yaml')
makedepends=('git' 'poetry')
source=("$pkgname-$pkgver.tar.gz::https://github.com/roovio/$pkgname/archive/$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$pkgname-$pkgver"

  # Use poetry to build the package
  poetry build -v -n
}

package() {
  cd "$pkgname-$pkgver"

  # Use poetry to package the application into a .tar.gz or .whl file
  # Then install it to the package directory using pip
  poetry export -f requirements.txt --output requirements.txt
  pip install --no-deps --root="$pkgdir/" --prefix=/usr dist/*.whl

  # Install license file
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
